"""COMPANY CULTURE — rated by VERIFIED EMPLOYEES (invite-code joined), anonymous, aggregated only when n >= K_MIN.
Two parts
  A. WORK DNA OF THE JOB (how the work actually is, 1-5) — same dimensions as Role Work DNA, so a candidate's Work DNA can be compared with REPORTED reality instead of an illustrative profile.
  B. CULTURE HEALTH (1-5, higher = better) → culture rating 0-100.
Evidence status: SELF-REPORTED by employees (PROPOSED instrument, not validated, not a certification, not a measurement of the company). Never used to rate individuals, never feeds hiring/rejection."""
import time, numpy as np
from scipy import stats
import vault

K_MIN = vault.K_MIN
JOB = [  # (dim, text, low anchor, high anchor)  — describes the JOB as it is
    ("communication", "How much of your work involves explaining results to non-technical people?", "Almost none", "Constantly"),
    ("collaboration", "How much of your work is done together with others rather than alone?", "Mostly solo", "Mostly with a team"),
    ("work_ethic", "How much rigour and detail-checking does the team expect before results are shared?", "Light", "Very high"),
    ("autonomy", "How much freedom do you have to decide your own next steps?", "Close direction", "Full ownership"),
    ("adaptability", "How often does the team change its approach or tools mid-project?", "Rarely", "Very often"),
    ("ambiguity", "How often do priorities change or work arrive loosely defined?", "Rarely", "Constantly"),
    ("pace", "How often do several tight deadlines land at the same time?", "Rarely", "Very often"),
    ("structure", "How defined are processes, documentation and planning?", "Loose", "Highly defined"),
    ("feedback", "How frequent and direct is feedback on your work?", "Rare", "Frequent and direct"),
    ("empathy", "How much does the work involve considering other people's / users' views?", "Little", "A great deal"),
    ("intensity", "How long and unpredictable are working hours in practice?", "Predictable", "Long / unpredictable"),
]
HEALTH = [  # higher = better
    ("safety", "I can disagree with a senior person or admit a mistake without fear of punishment.", "Strongly disagree", "Strongly agree"),
    ("fairness", "Workload, credit and promotion decisions are handled fairly.", "Strongly disagree", "Strongly agree"),
    ("growth", "I am learning and my skills are growing here.", "Strongly disagree", "Strongly agree"),
    ("leadership", "Leaders explain decisions and follow through on what they say.", "Strongly disagree", "Strongly agree"),
    ("recognition", "Good work is noticed and acknowledged.", "Strongly disagree", "Strongly agree"),
    ("boundaries", "Time off and off-hours are respected in practice.", "Strongly disagree", "Strongly agree"),
]
ITEMS = [("job",) + x for x in JOB] + [("health",) + x for x in HEALTH]
HEALTH_LABEL = {"safety": "Psychological safety", "fairness": "Fairness", "growth": "Growth", "leadership": "Leadership trust", "recognition": "Recognition", "boundaries": "Respect for boundaries"}
JOB_DIMS = [d for d, *_ in JOB]
STATUS = "SELF-REPORTED by verified employees · anonymous · PROPOSED instrument, not validated · not a certification of the company"


def cycle(ts=None):
    t = time.gmtime(ts or time.time()); return f"{t.tm_year}-Q{(t.tm_mon - 1) // 3 + 1}"


def _ids(): return [x[1] for x in ITEMS]


def submit(user, answers: dict, ts=None):
    """store one anonymous response (no user id in the row). → (ok, message)."""
    if not user or user.get("role") != "EMPLOYEE" or not user.get("org_id"): return False, "Only verified employees can rate their organisation."
    miss = [i for i in _ids() if answers.get(i) not in (1, 2, 3, 4, 5)]
    if miss: return False, f"Please answer all {len(ITEMS)} items ({len(miss)} left)."
    cyc = cycle(ts); con = vault.db()
    try:
        con.execute("BEGIN IMMEDIATE")
        u = con.execute("SELECT submitted_cycle FROM users WHERE id=?", (user["id"],)).fetchone()
        if u and u["submitted_cycle"] == cyc: con.rollback(); return False, f"You have already submitted for {cyc}. Responses are anonymous and cannot be edited."
        blob = vault.encrypt({i: int(answers[i]) for i in _ids()}, f"culture:{user['org_id']}:{cyc}")
        con.execute("INSERT INTO culture_responses(org_id,cycle,blob) VALUES(?,?,?)", (user["org_id"], cyc, blob))
        con.execute("UPDATE users SET submitted_cycle=? WHERE id=?", (cyc, user["id"])); con.commit()
        return True, "Thank you — your response was encrypted and stored anonymously."
    except Exception:
        con.rollback(); raise
    finally: con.close()


def _load(org_id, cyc):
    con = vault.db()
    try: rows = con.execute("SELECT blob FROM culture_responses WHERE org_id=? AND cycle=?", (org_id, cyc)).fetchall()
    finally: con.close()
    return [vault.decrypt(r["blob"], f"culture:{org_id}:{cyc}") for r in rows]


def count(org_id, cyc=None):
    con = vault.db()
    try: return con.execute("SELECT COUNT(*) n FROM culture_responses WHERE org_id=? AND cycle=?", (org_id, cyc or cycle())).fetchone()["n"]
    finally: con.close()


def _ci(v):
    v = np.asarray(v, float); n = len(v); m = float(v.mean())
    if n < 2: return m, m, m
    h = float(stats.t.ppf(0.975, n - 1) * v.std(ddof=1) / np.sqrt(n)); return m, max(1.0, m - h), min(5.0, m + h)


def aggregate(org_id, cyc=None):
    """k-anonymity gate: below K_MIN responses NOTHING but the count is returned."""
    cyc = cyc or cycle(); n = count(org_id, cyc)
    if n < K_MIN: return dict(suppressed=True, n=n, need=K_MIN, cycle=cyc)
    rs = _load(org_id, cyc); out = {}
    for i in _ids():
        m, lo, hi = _ci([r[i] for r in rs]); out[i] = dict(mean=m, lo=lo, hi=hi)
    health = [out[d]["mean"] for d, *_ in HEALTH]; rating = round(100 * (float(np.mean(health)) - 1) / 4)
    stab = {d: out[d] for d in JOB_DIMS}
    return dict(suppressed=False, n=n, cycle=cyc, items=out, rating=rating, job_profile={d: out[d]["mean"] for d in JOB_DIMS}, health={d: out[d] for d, *_ in HEALTH})


def published_orgs(cyc=None):
    con = vault.db()
    try: orgs = con.execute("SELECT id,name,simulated FROM orgs WHERE published=1 ORDER BY name").fetchall()
    finally: con.close()
    res = []
    for o in orgs:
        a = aggregate(o["id"], cyc)
        if not a["suppressed"]: res.append(dict(org_id=o["id"], name=o["name"], simulated=bool(o["simulated"]), agg=a))
    return res


def set_published(org_id, flag: bool):
    con = vault.db()
    try: con.execute("UPDATE orgs SET published=? WHERE id=?", (1 if flag else 0, org_id)); con.commit()
    finally: con.close()


def is_published(org_id):
    con = vault.db()
    try: r = con.execute("SELECT published FROM orgs WHERE id=?", (org_id,)).fetchone(); return bool(r and r["published"])
    finally: con.close()


def discussion_areas(agg, k=3):
    """lowest-rated health items + highest-demand job dims → prompts for a conversation, not a verdict."""
    if agg["suppressed"]: return [], []
    low = sorted(HEALTH, key=lambda x: agg["items"][x[0]]["mean"])[:k]
    hi = sorted(JOB, key=lambda x: -agg["items"][x[0]]["mean"])[:k]
    return [(HEALTH_LABEL[d], agg["items"][d]["mean"]) for d, *_ in low], [(d, agg["items"][d]["mean"]) for d, *_ in hi]
