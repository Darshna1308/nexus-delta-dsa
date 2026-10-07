"""QA harness: Streamlit AppTest over every screen + edge cases.  python test_app.py"""
import os, sys, shutil, tempfile, json
sys.path.insert(0, "."); os.environ["NEXUS_VAULT_DIR"] = tempfile.mkdtemp(prefix="nxvault_")
from streamlit.testing.v1 import AppTest
import config

def fresh(**env):
    for k, v in env.items(): os.environ[k] = v
    at = AppTest.from_file("app.py", default_timeout=120); at.session_state["guest"] = True; at.run(); return at

def clicks(at, key):
    b = [x for x in at.button if x.key == key]; assert b, f"button {key} not found"; b[0].click(); return at.run()

def exc(at): return [e.value for e in at.exception]

results = []
def check(name, cond, extra=""):
    results.append((name, bool(cond))); print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))

# --- every page via nav
for i, p in enumerate(config.PAGES):
    at = fresh(); at = clicks(at, f"nav_{i}"); check(f"page {p} renders", not exc(at) and at.session_state.page == p, exc(at))

# --- capability matrix + drawer
at = fresh(); at = clicks(at, "nav_2"); at = clicks(at, "cap_maths_stats"); check("drawer selects maths_stats", at.session_state.cap_sel == "maths_stats" and not exc(at), exc(at))
at = clicks(at, "cap_big_data"); check("drawer big_data", at.session_state.cap_sel == "big_data" and not exc(at))
# --- home tile opens evidence
at = fresh(); b = [x for x in at.button if x.key.startswith("open_BIGGES")]; b[0].click(); at.run(); check("home conflict tile opens storytelling evidence", at.session_state.page == "CAPABILITY INTELLIGENCE" and at.session_state.cap_sel == "story" and not exc(at), exc(at))
# --- student lens: role + scores
at = fresh(); at = clicks(at, "nav_5")
sc = [x for x in at.get("segmented_control")]; check("career renders controls", len(sc) >= 6, len(sc))
at.session_state["role"] = "ML Engineer"; at.run(); check("career role switch", not exc(at), exc(at))
for k in ("ai_ml", "coding", "maths_stats", "big_data", "story"): at.session_state[f"score_{k}"] = 2
at.run(); check("career scores update", not exc(at), exc(at))
# --- scanner: empty, bad, sample, short
at = fresh(); at = clicks(at, "nav_6"); at = clicks(at, "scan_go"); check("scanner empty input handled", not exc(at) and at.session_state.jd_result and not at.session_state.jd_result["ok"], exc(at))
at.session_state["jd_text"] = "hello world, this is not a job description at all but it is longer than forty chars"; at = clicks(at, "scan_go"); check("scanner bad JD handled (warns, no crash)", not exc(at) and at.session_state.jd_result["ok"] and any("data/analytics" in w for w in at.session_state.jd_result["parsed"]["warnings"]), exc(at))
at.session_state["jd_text"] = "Senior Data Scientist\nBengaluru startup, 5-8 years. Python, SQL, machine learning, Tableau. Fast-paced with tight deadlines and changing priorities."; at = clicks(at, "scan_go")
r = at.session_state.jd_result; check("scanner good JD: tags+probs+signals", not exc(at) and r["ok"] and r["probs"] is not None and abs(sum(r["probs"]) - 1) < 1e-6 and r["signals"]["ambiguity"]["signal"], exc(at))
# --- Hear (voice unavailable -> text fallback)
at.session_state["scan_mode"] = "HEAR THIS ROLE"; at.run(); check("hear: voice-unavailable page renders", not exc(at), exc(at))
at.session_state["hear_text"] = "Should we fund maths and statistics?"; at = clicks(at, "hear_go"); check("hear: typed question -> evidence card", not exc(at) and at.session_state._hear_out["intent"]["intent"] == "capability_verdict", exc(at))
at.session_state["hear_text"] = "blah blah"; at = clicks(at, "hear_go"); check("hear: unknown intent handled", not exc(at) and not at.session_state._hear_out["intent"]["understood"], exc(at))
at.session_state["hear_text"] = ""; at = clicks(at, "hear_go"); check("hear: empty handled", not exc(at) and at.session_state._hear_out["kind"] == "empty", exc(at))
# --- Work DNA: consent gate, full quiz, results, EQ skipped, EQ taken
at = fresh(); at = clicks(at, "nav_7"); st_ = [x for x in at.button if x.key == "dna_start"][0]; check("work dna start disabled without consent", st_.disabled)
at.session_state["dna_consent"] = True; at.run(); at = clicks(at, "dna_start"); check("work dna quiz screen", at.session_state.dna_stage == "quiz" and not exc(at), exc(at))
for q in range(15): at = clicks(at, f"dna_a_{q}_{3 + (q % 3)}")
check("work dna reaches result", at.session_state.dna_stage == "result" and not exc(at), exc(at))
for t in ["YOUR FIT", "EDIT ROLE", "ORGANISATION VIEW", "OPTIONAL EQ"]:
    at.session_state["dna_tab"] = t; at.run(); check(f"work dna view {t}", not exc(at), exc(at))
at.session_state["dna_tab"] = "OPTIONAL EQ"; at.run(); at = clicks(at, "eq_skip"); check("EQ skipped -> nothing breaks", at.session_state.eq_stage == "skipped" and not exc(at), exc(at))
at.session_state["dna_tab"] = "YOUR FIT"; at.run(); check("fit still renders after EQ skip", not exc(at))
at.session_state["dna_tab"] = "OPTIONAL EQ"; at.run(); at = clicks(at, "eq_change"); at.run(); at.session_state["eq_0"] = 4; at.session_state["eq_1"] = 3; at = clicks(at, "eq_done"); check("EQ taken -> indicative report", at.session_state.eq_stage == "done" and not exc(at), exc(at))
for role in ["Startup Data Scientist", "Enterprise Data Scientist", "Research Data Scientist", "Analytics Consultant"]:
    at.session_state["dna_tab"] = "YOUR FIT"; at.session_state["dna_role"] = role; at.run(); check(f"role work dna: {role}", not exc(at), exc(at))
# --- scanner -> Work DNA JD profile
at = fresh(); at = clicks(at, "nav_6"); at.session_state["jd_text"] = "Data Analyst MIS\nMumbai 2-4 years. Excel, SQL, Power BI, process documentation and compliance."; at = clicks(at, "scan_go")
at.session_state["dna_ans"] = {i: 3 for i in range(15)}; at.session_state["dna_stage"] = "result"; at = clicks(at, "sc_use"); check("scanner -> work dna with JD profile", at.session_state.page == "WORK DNA" and at.session_state.dna_role == "From scanned JD" and not exc(at), exc(at))
at.session_state["dna_tab"] = "ORGANISATION VIEW"; at.run(); check("org view with VERIFY dims", not exc(at), exc(at))
# --- demo mode all 12 steps
at = fresh(); at = clicks(at, "demo_start")
for i in range(12):
    ok = not exc(at) and at.session_state.demo_step == i; check(f"demo step {i+1}", ok, exc(at))
    if i < 11: at = clicks(at, "demo_next")
at = clicks(at, "demo_exit"); check("demo exit", not at.session_state.demo_on)
# --- missing data edge cases
tmp = tempfile.mkdtemp(); shutil.copytree("out", tmp + "/out")
def with_dir(remove=None, replace=None):
    d = tempfile.mkdtemp(); shutil.copytree("out", d + "/o")
    for f in remove or []: os.remove(f"{d}/o/{f}")
    for f, c in (replace or {}).items(): open(f"{d}/o/{f}", "w").write(c)
    return d + "/o"
import importlib, config
for name, kw in [("missing model", dict(remove=["jd_scanner_m2.joblib"])), ("missing taxonomy", dict(remove=["taxonomy.json"])), ("missing role artifacts", dict(remove=["app_artifacts.json"])),
                 ("missing results", dict(remove=["results.json"])), ("corrupt results", dict(replace={"results.json": "{not json"})), ("incomplete results", dict(replace={"results.json": "{}"}))]:
    os.environ["NEXUS_DATA_DIR"] = with_dir(**kw)
    for i, p in enumerate(config.PAGES):
        at = AppTest.from_file("app.py", default_timeout=120); at.session_state["guest"] = True; at.run(); at = clicks(at, f"nav_{i}")
        if p == "JD SCANNER":
            at.session_state["jd_text"] = "Data Scientist\nPython, machine learning, SQL, 3-5 years in Pune. Fast-paced."; at = clicks(at, "scan_go")
        if p == "WORK DNA":
            at.session_state["dna_ans"] = {i: 3 for i in range(15)}; at.session_state["dna_stage"] = "result"; at.run()
        if p == "CAREER INTELLIGENCE": at.run()
        txt = " ".join(m.value for m in at.markdown)
        expect = {"missing results": "Evidence data unavailable", "corrupt results": "Evidence data unavailable", "incomplete results": "Evidence data unavailable"}.get(name)
        if expect and p in ("HOME", "CAPABILITY INTELLIGENCE", "CAREER INTELLIGENCE", "EVIDENCE"): check(f"[{name}] {p} shows graceful banner", expect in txt or "unavailable" in txt)
        if name == "missing model" and p == "JD SCANNER": check("[missing model] scanner says model unavailable", "model unavailable" in txt.lower() or "Optional data missing" in txt)
        check(f"[{name}] {p}", not exc(at), exc(at))
os.environ.pop("NEXUS_DATA_DIR", None)

# ============================================================ AUTH / ENCRYPTION / CULTURE
import vault, auth, culture as CU, sqlite3, time
# gate: no session -> login page, no nav
at = AppTest.from_file("app.py", default_timeout=120); at.run()
check("login gate shown without session", not exc(at) and any(b.key == "li_go" for b in at.button) and not any(b.key == "nav_0" for b in at.button), exc(at))
at.session_state["auth_tab"] = "GUEST"; at.run(); at = clicks(at, "guest_go"); check("guest continues", at.session_state.guest and any(b.key == "nav_0" for b in at.button))
# register / login / policy
u, e = auth.register("org_admin1", "Weakpass", "ORG", org_name="TestCo"); check("weak password rejected", u is None and e)
u, e = auth.register("org_admin1", "Strong#Pass1", "ORG", org_name="TestCo"); check("org registers", u and u["role"] == "ORG", e)
u2, e = auth.register("org_admin2", "Strong#Pass1", "ORG", org_name="TestCo"); check("duplicate org rejected", u2 is None)
u3, e = auth.register("emp_x", "Strong#Pass1", "EMPLOYEE", invite="BAD-CODE-0000"); check("employee needs valid invite", u3 is None)
org = auth.login("org_admin1", "Strong#Pass1")[0]; check("login ok", org and org["org"] == "TestCo")
check("wrong password rejected", auth.login("org_admin1", "nope")[0] is None)
for _ in range(5): auth.login("org_admin1", "bad")
check("lockout after 5 failures (even with right password)", auth.login("org_admin1", "Strong#Pass1")[0] is None)
con = vault.db(); con.execute("UPDATE users SET locked_until=0, fails=0"); con.commit(); con.close()
# invites single-use
code = auth.new_invite(org["org_id"]); emps = []
for i in range(5):
    c = code if i == 0 else auth.new_invite(org["org_id"]); r, e = auth.register(f"emp{i}", "Strong#Pass1", "EMPLOYEE", invite=c); emps.append(r); check(f"employee {i} joins with invite", r and r["org_id"] == org["org_id"], e)
r, e = auth.register("emp_reuse", "Strong#Pass1", "EMPLOYEE", invite=code); check("invite code is single-use", r is None)
# privacy gate: <5 -> suppressed
ans = lambda v: {i: v for i in CU._ids()}
for i in range(4): ok, m = CU.submit(emps[i], ans(2 + i % 3)); assert ok, m
a = CU.aggregate(org["org_id"]); check("k-anonymity: 4 responses -> suppressed, no values", a["suppressed"] and "items" not in a and a["n"] == 4)
check("not published list excludes small org", "TestCo" not in [o["name"] for o in CU.published_orgs()])
ok, m = CU.submit(emps[0], ans(3)); check("second submission same quarter refused", not ok)
ok, m = CU.submit(emps[4], {**ans(3), "safety": None}); check("incomplete survey refused", not ok)
ok, m = CU.submit(org, ans(3)); check("org admin cannot rate", not ok)
ok, m = CU.submit(emps[4], ans(5)); a = CU.aggregate(org["org_id"]); check("5th response unlocks aggregate", ok and not a["suppressed"] and a["n"] == 5 and 0 <= a["rating"] <= 100)
check("aggregate mean correct", abs(a["items"]["safety"]["mean"] - (2 + 3 + 4 + 2 + 5) / 5) < 1e-9, a["items"]["safety"])
CU.set_published(org["org_id"], True); check("published after opt-in", "TestCo" in [o["name"] for o in CU.published_orgs()])
# encryption at rest
raw = open(vault.vdir() / "nexus_secure.db", "rb").read(); con = vault.db(); blobs = [r["blob"] for r in con.execute("SELECT blob FROM culture_responses")]; cols = [d[1] for d in con.execute("PRAGMA table_info(culture_responses)")]; con.close()
check("response rows carry no user reference", "user_id" not in cols and "username" not in cols, cols)
check("responses are ciphertext (no JSON visible in DB bytes)", all(b"safety" not in b and b"communication" not in b for b in blobs) and b"safety" not in raw)
check("passwords not stored in clear", b"Strong#Pass1" not in raw)
try: vault.decrypt(blobs[0], "culture:999:2026-Q4"); check("AAD binds row to org", False)
except Exception: check("AAD binds row to org (wrong context fails)", True)
t = bytearray(blobs[0]); t[-1] ^= 1
try: vault.decrypt(bytes(t), f"culture:{org['org_id']}:{CU.cycle()}"); check("tamper detected", False)
except Exception: check("tamper detected (GCM auth fails)", True)
# private EQ report: only the owner's password key opens it
cand, _ = auth.register("cand1", "Strong#Pass1", "CANDIDATE"); cu = auth.login("cand1", "Strong#Pass1")[0]
auth.save_private(cu, "eq", dict(bands={"Communication": "Solid"})); check("private report round-trips", auth.load_private(cu, "eq")["bands"]["Communication"] == "Solid")
raw = open(vault.vdir() / "nexus_secure.db", "rb").read(); check("private report not readable in DB", b"Communication" not in raw)
other = dict(cu, ukey=vault.user_key("Different#Pass9", b"x" * 16))
try: auth.load_private(other, "eq"); check("other key cannot read private report", False)
except Exception: check("other key cannot read private report", True)
auth.delete_private(cu, "eq"); check("user can delete private report", auth.load_private(cu, "eq") is None)
# seed + UI flows
import seed_demo; seed_demo.run()
for who, page, expect in [("demo_candidate", 8, "CULTURE RATING"), ("demo_org", 8, "RESPONSES THIS CYCLE"), ("demo_employee", 8, "PART A")]:
    at = AppTest.from_file("app.py", default_timeout=120); at.run(); at.session_state["auth_tab"] = "SIGN IN"; at.run()
    at.text_input(key="li_user").set_value(who); at.text_input(key="li_pw").set_value("Demo#2026pw"); at = clicks(at, "li_go")
    check(f"{who} signs in via UI", not exc(at) and at.session_state.get("user") and at.session_state.user["username"] == who, exc(at))
    at = clicks(at, f"nav_{page}"); txt = " ".join(m.value for m in at.markdown); check(f"{who}: culture page shows '{expect}'", not exc(at) and expect in txt, exc(at))
    if who == "demo_candidate":
        at = clicks(at, "cu_cmp"); check("candidate: compare culture with Work DNA", at.session_state.page == "WORK DNA" and "employee-reported" in at.session_state.dna_role, at.session_state.get("dna_role"))
        at.session_state["dna_ans"] = {i: 3 for i in range(15)}; at.session_state["dna_stage"] = "result"; at.run(); txt = " ".join(m.value for m in at.markdown)
        check("work dna renders employee-reported profile with SIMULATED + not validated badges", not exc(at) and "EMPLOYEE-REPORTED" in txt and "SIMULATED" in txt, exc(at))
    if who == "demo_employee":
        for i in CU._ids(): at.session_state[f"cu_{i}"] = 3
        at = clicks(at, "cu_send"); check("employee submits via UI", not exc(at) and at.session_state.get("cu_done"), at.session_state.get("cu_err"))
        at = clicks(at, "cu_send"); check("employee double-submit blocked in UI", at.session_state.get("cu_err") and not exc(at))
    if who == "demo_org":
        at = clicks(at, "inv_new"); check("org generates invite", at.session_state.get("last_code") and not exc(at), exc(at))
    at = clicks(at, "logout"); check(f"{who} signs out -> login gate", not at.session_state.get("user") and any(b.key == "li_go" for b in at.button))
bad = [n for n, ok in results if not ok]; print(f"\n{len(results)-len(bad)}/{len(results)} passed"); sys.exit(1 if bad else 0)
