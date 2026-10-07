"""WORK DNA — work-style fit and friction (PROPOSED, not validated). Not a medical or personality diagnosis, not burnout prediction, never auto-hire/auto-reject.
User self-assessment (15 items, 13 work-style dimensions) is compared with a ROLE WORK DNA (illustrative profile, or cues read from a scanned JD)."""
import numpy as np

DIMS = {"communication": "Communication", "collaboration": "Collaboration", "work_ethic": "Work Ethic / Conscientiousness", "adaptability": "Adaptability", "autonomy": "Autonomy",
        "structure": "Structure Preference", "ambiguity": "Ambiguity Tolerance", "pace": "Pace / Deadline Tolerance", "feedback": "Feedback Orientation",
        "learning": "Learning Agility", "social": "Social Energy", "recovery": "Recovery / Work-Life Boundary", "empathy": "Perspective-taking"}

QUESTIONS = [  # (dim, text, low anchor, high anchor)
    ("communication", "How comfortable are you explaining a technical result to people who are not technical?", "I'd rather avoid it", "I enjoy it"),
    ("communication", "How naturally do you turn an analysis into a clear written summary or a short presentation?", "It takes real effort", "It comes easily"),
    ("collaboration", "How much do you prefer solving problems together with a team rather than alone?", "Mostly alone", "Mostly together"),
    ("work_ethic", "When a task is 'good enough', how likely are you to keep checking the details until it is right?", "Rarely", "Almost always"),
    ("adaptability", "How quickly do you change your approach when the first plan stops working?", "Slowly", "Immediately"),
    ("autonomy", "How comfortable are you working with little supervision and deciding your own next steps?", "Prefer clear direction", "Prefer to own it"),
    ("structure", "How much do you like clearly defined processes, documentation and checklists?", "Dislike them", "Need them"),
    ("structure", "How much does a detailed plan with fixed milestones help you do your best work?", "Not at all", "Very much"),
    ("ambiguity", "How comfortable are you when project priorities change without warning?", "Prefer strong structure", "Comfortable with ambiguity"),
    ("pace", "How well do you work when several tight deadlines land in the same week?", "It drains me", "It energises me"),
    ("feedback", "How comfortable are you receiving frequent, direct feedback on your work?", "Uncomfortable", "I actively seek it"),
    ("learning", "How quickly do you pick up an unfamiliar tool or method when the job needs it?", "Slowly", "Quickly"),
    ("social", "After a full day of meetings and conversations, how much energy do you have left?", "Very little", "Plenty"),
    ("recovery", "How important is it to you to have predictable hours and protected time off?", "I'm flexible", "Essential"),
    ("empathy", "When a decision affects other people, how much do you actively consider their point of view?", "Rarely", "Almost always"),
]
N_Q = len(QUESTIONS)

# comparison rows: (role_dim, label, rule). one-sided: friction only when the ROLE demands more than YOU report. two-sided: any large mismatch.
COMPARE = [("communication", "Communication", "one"), ("collaboration", "Collaboration", "one"), ("work_ethic", "Work Ethic", "one"), ("autonomy", "Autonomy", "two"),
           ("adaptability", "Adaptability", "one"), ("ambiguity", "Ambiguity", "one"), ("pace", "Pace", "one"), ("structure", "Structure", "two"), ("feedback", "Feedback", "one"),
           ("empathy", "Perspective-taking", "one"), ("intensity", "Work intensity", "one"), ("social", "Social load", "one")]
RADAR_DIMS = [c[0] for c in COMPARE[:10]]
STRONG, WATCH = 0.75, 1.5

ROLE_PROFILES = {  # SIMULATED / ILLUSTRATIVE — hand-written, NOT company measurements
    "Startup Data Scientist": dict(communication=4, collaboration=4, work_ethic=4, autonomy=5, adaptability=5, ambiguity=5, pace=5, structure=2, feedback=3, empathy=3, intensity=4),
    "Enterprise Data Scientist": dict(communication=3, collaboration=4, work_ethic=4, autonomy=3, adaptability=3, ambiguity=2, pace=3, structure=5, feedback=4, empathy=3, intensity=2),
    "Research Data Scientist": dict(communication=3, collaboration=3, work_ethic=5, autonomy=5, adaptability=3, ambiguity=4, pace=2, structure=3, feedback=4, empathy=2, intensity=3),
    "Analytics Consultant": dict(communication=5, collaboration=5, work_ethic=4, autonomy=3, adaptability=5, ambiguity=4, pace=5, structure=3, feedback=4, empathy=5, intensity=4),
}
ROLE_DIM_LABEL = {**{k: v for k, v in DIMS.items()}, "intensity": "Work intensity", "social": "Social load"}

PHRASE = {  # dim -> (role-high, user-low, role-low, user-high)
    "communication": ("frequent explanation of results to non-technical people", "lower comfort explaining results", "little stakeholder communication", "a strong preference for communicating"),
    "collaboration": ("constant team collaboration", "a preference for working alone", "mostly solo work", "a preference for working with others"),
    "work_ethic": ("very high rigour and detail checking", "a lower detail-checking habit", "light quality control", "a strong detail-checking habit"),
    "autonomy": ("a lot of self-direction with little supervision", "a preference for clear direction", "close direction and supervision", "a preference for owning decisions"),
    "adaptability": ("frequent changes of approach", "slower adjustment when plans fail", "stable approaches", "very quick adjustment"),
    "ambiguity": ("frequent priority changes and loosely defined work", "a preference for predictable structure", "stable, well-defined work", "high comfort with ambiguity"),
    "pace": ("several tight deadlines at once", "lower comfort with deadline pressure", "a relaxed delivery pace", "high comfort with deadline pressure"),
    "structure": ("highly defined processes and documentation", "a preference for flexibility", "loose, undefined processes", "a strong preference for structure"),
    "feedback": ("frequent, direct feedback", "lower comfort with frequent feedback", "infrequent feedback", "a strong wish for frequent feedback"),
    "empathy": ("constant consideration of other people's views", "less habitual perspective-taking", "little people-impact", "strong habitual perspective-taking"),
    "intensity": ("long, unpredictable hours", "a strong need for predictable hours and time off", "predictable hours", "flexibility on hours"),
    "social": ("heavy daily social/meeting load", "limited social energy", "low social load", "plenty of social energy"),
}
FRICTION_NAME = {"ambiguity": "High ambiguity friction", "pace": "High pace friction", "structure": "Structure mismatch", "social": "Social-load friction", "intensity": "Work-intensity / boundary friction",
                 "autonomy": "Autonomy mismatch", "communication": "Communication-demand friction", "collaboration": "Collaboration-demand friction", "work_ethic": "Rigour-demand friction",
                 "adaptability": "Adaptability-demand friction", "feedback": "Feedback-style friction", "empathy": "Perspective-taking demand"}
EMPLOYER_Q = {
    "ambiguity": ["How often do priorities change, and who decides when they do?", "How is work scoped when requirements are still unclear?"],
    "pace": ["How are deadlines handled when scope changes?", "How many deliverables are usually in flight at once?"],
    "structure": ["How defined are processes and documentation — what is written down vs. learned on the job?", "Is there a standard way projects are planned and reviewed?"],
    "autonomy": ["How much direction does a new joiner get in the first three months?", "Who do I go to when I'm blocked, and how quickly do they respond?"],
    "social": ["How many meetings does a typical week include, and how much uninterrupted deep-work time is normal?", "What does a typical day look like in terms of collaboration vs focus time?"],
    "intensity": ["How is after-hours work handled, and is on-call expected?", "How are time off and workload peaks managed?"],
    "communication": ["How often do analysts present to non-technical stakeholders?", "Is there support for presentation and storytelling skills?"],
    "collaboration": ["How is work split between the team and individual ownership?", "How do team members collaborate day to day?"],
    "work_ethic": ["What quality-review process do results go through before they are shared?"],
    "adaptability": ["How often do tools or methods change, and how is onboarding done?"],
    "feedback": ["How is performance evaluated, and how often is feedback given?", "Is feedback written, verbal, or both?"],
    "empathy": ["How much customer/user contact does the role involve?"],
}
GENERIC_Q = ["How is performance evaluated?"]


def score_answers(ans: dict) -> dict:
    """ans: {question_index: 1..5}. → dim → mean score (only dims with at least one answer)."""
    acc = {}
    for i, v in ans.items():
        if v is None: continue
        acc.setdefault(QUESTIONS[int(i)][0], []).append(float(v))
    return {d: float(np.mean(v)) for d, v in acc.items()}


def role_full(role: dict) -> dict:
    """add derived 'social' load = mean(collaboration, communication)."""
    r = dict(role); r["social"] = (r.get("collaboration", 3) + r.get("communication", 3)) / 2.0; r.setdefault("intensity", 3); return r


def user_value(dim: str, you: dict):
    if dim == "intensity": return None if "recovery" not in you else 6.0 - you["recovery"]   # strong need for boundaries = low tolerance for intensity
    return you.get(dim)


def compare(you: dict, role: dict, thin: set = None) -> dict:
    """returns rows + summary. thin = role dims with no cue in a JD-derived profile (shown as VERIFY, excluded from fit)."""
    role = role_full(role); thin = thin or set(); rows = []
    for dim, label, rule in COMPARE:
        yv, rv = user_value(dim, you), role.get(dim)
        if yv is None or rv is None: continue
        diff = rv - yv; eff = max(0.0, diff) if rule == "one" else abs(diff)
        if dim in thin: status = "VERIFY"
        else: status = "STRONG FIT" if eff <= STRONG else ("WATCH" if eff <= WATCH else "HIGH FRICTION")
        if dim == "structure" and diff < 0: name = "Over-structured for you"
        elif dim == "structure": name = "Low-structure friction"
        elif dim == "autonomy" and diff < 0: name = "Close direction vs. your preference to own work"
        else: name = FRICTION_NAME[dim]
        rows.append(dict(dim=dim, label=label, role=float(rv), you=float(yv), gap=float(diff), effective_gap=float(eff), status=status, friction=name, rule=rule))
    scored = [r for r in rows if r["status"] != "VERIFY"]
    fit = None if not scored else round(100 * (1 - float(np.mean([min(r["effective_gap"], 4.0) for r in scored])) / 4.0))
    high = [r for r in scored if r["status"] == "HIGH FRICTION"]; watch = [r for r in scored if r["status"] == "WATCH"]
    if fit is None: level = "UNDETERMINED"
    elif len(high) >= 2 or fit < 60: level = "HIGH FRICTION"
    elif len(high) == 1 or len(watch) >= 3 or fit < 75: level = "MODERATE FRICTION"
    else: level = "LOW FRICTION"
    flagged = sorted(high + watch, key=lambda r: -r["effective_gap"])
    strengths = [r["label"] for r in sorted([r for r in scored if r["status"] == "STRONG FIT"], key=lambda r: -r["you"])[:3]]
    if you.get("learning", 0) >= 4 and "Learning agility" not in strengths: strengths = (strengths[:2] + ["Learning agility"]) if len(strengths) >= 3 else strengths + ["Learning agility"]
    qs = []
    for r in flagged[:3]:
        qs += EMPLOYER_Q.get(r["dim"], [])[:2]
    qs = (qs + GENERIC_Q)[:7]
    sentence = None
    if flagged:
        r = flagged[0]; ph = PHRASE[r["dim"]]
        if r["rule"] == "two" and r["gap"] < 0: sentence = f"Potential sustainability concern: the role offers {ph[2]} while your assessment indicates {ph[3]}."
        elif r["rule"] == "two": sentence = f"Potential sustainability concern: the role needs {ph[0]} while your assessment indicates {ph[1]}."
        else: sentence = f"Potential sustainability concern: the role requires {ph[0]} while your assessment indicates {ph[1]}."
    nxt = (f"Ask the recruiter: “{EMPLOYER_Q[flagged[0]['dim']][0]}” before accepting this role." if flagged and EMPLOYER_Q.get(flagged[0]["dim"]) else "No major friction flagged — still ask how performance is evaluated.")
    return dict(rows=rows, fit=fit, level=level, flagged=flagged, strengths=strengths, watchouts=[r["label"] for r in flagged], questions=qs, sentence=sentence, next_action=nxt, n_high=len(high), n_watch=len(watch))


ALIGNMENT = {"STRONG FIT": "STRONG ALIGNMENT", "WATCH": "DISCUSSION AREA", "HIGH FRICTION": "POTENTIAL FRICTION", "VERIFY": "VERIFY"}
