"""Career Intelligence: development priorities from market evidence + entered scores + role demand. NEVER uses the one-company JDS outcome model to predict an individual."""
import math
import config
from config import LABEL, CAPS
from decision_engine import build_matrix, market_ci

ROLES = ["Data Scientist", "Data Analyst", "ML Engineer", "Data Engineer", "Analytics Consultant"]
TIERS = ["HIGH PRIORITY", "STRATEGIC", "STRENGTHEN", "MAINTAIN", "LOW EVIDENCE"]
TIER_RULES = [
    ("HIGH PRIORITY", "Gap ≥ 1.5 AND market premium AND ≥ 25% of this role's postings ask for it."),
    ("STRATEGIC", "Gap ≥ 0.75 AND (market premium OR the capability is 'fund with reframe')."),
    ("STRENGTHEN", "Gap ≥ 0.75 but no robust premium — kept because the role itself asks for it (≥ 40% of postings)."),
    ("MAINTAIN", "Gap < 0.75: you are near the top of the scale already."),
    ("LOW EVIDENCE", "Gap ≥ 0.75 but neither a robust market premium, an internal signal, nor strong role demand."),
]


def role_info(art: dict, role: str) -> dict:
    return (art or {}).get("roles", {}).get(role) or {}


def priority_plan(results: dict, art: dict, role: str, scores: dict) -> list:
    rows = {r["key"]: r for r in build_matrix(results)}
    info = role_info(art, role); demand = info.get("capability_share", {})
    plan = []
    for k in CAPS:
        r = rows.get(k)
        if not r: continue
        s = float(scores.get(k, 3.0)); gap = round(5.0 - s, 2); d = demand.get(k)
        orr, lo, hi = market_ci(results, k)
        premium = r["market"] == "Premium"; reframe = r["verdict"] == "FUND WITH REFRAME"
        dd = d if d is not None else 0.0
        if gap < 0.75: tier = "MAINTAIN"
        elif gap >= 1.5 and premium and dd >= 0.25: tier = "HIGH PRIORITY"
        elif premium or reframe: tier = "STRATEGIC"
        elif dd >= 0.40: tier = "STRENGTHEN"
        else: tier = "LOW EVIDENCE"
        score = gap * (1 + max(math.log(orr), 0) if orr else 1) * (0.5 + dd)
        if k == "story":
            mv = f"Broad family discounted (OR {orr:.2f}); visualisation-tool postings are not (OR {results['story_decomp']['viz']['OR']:.2f})" if results.get("story_decomp") else f"OR {orr:.2f}"
        else:
            mv = f"OR {orr:.2f} [{lo:.2f}, {hi:.2f}] — {r['market'].lower()}"
        why = {"HIGH PRIORITY": "Large personal gap on a capability the market rewards and this role asks for.",
               "STRATEGIC": ("Reframe toward visual analytics and decision communication, not generic MIS/reporting." if reframe else "The market rewards it; close the gap steadily."),
               "STRENGTHEN": "Role-required, but the market pay premium is not robust — build it to be credible, not for pay.",
               "MAINTAIN": "You are already near the top of the scale; keep it current.",
               "LOW EVIDENCE": "No robust market premium, no internal signal and low demand for this role — avoid prioritising it on evidence."}[tier]
        plan.append(dict(key=k, capability=LABEL[k], tier=tier, score=score, your_score=s, gap=gap, why=why, market_value=mv,
                         role_demand=d, cohort_headroom=r["headroom"], evidence=f"Market: {r['premium_specs']}/6 spec premium · role demand {dd:.0%} of {info.get('n_postings','?')} postings" if d is not None else f"Market: {r['premium_specs']}/6 spec premium",
                         limitation=("Association only; skill text is truncated in 87% of postings." if k != "story" else "MIS-only is also a role-level proxy; causality not tested."), verdict=r["verdict_display"]))
    plan.sort(key=lambda x: (TIERS.index(x["tier"]), -x["score"]))
    return plan


def technical_fit(scores: dict, art: dict, role: str = None, required: dict = None) -> dict:
    """Readiness index 0-100: coverage of required capability levels, weighted by demand. DERIVED, not a prediction.
    required: {cap: weight} (JD scan) — otherwise role demand from the data."""
    weights = dict(required) if required else dict((role_info(art, role).get("capability_share") or {}))
    if not weights: return dict(value=None, parts={})
    parts, num, den = {}, 0.0, 0.0
    for k in CAPS:
        w = max(float(weights.get(k, 0.0)), 0.05); target = 4.0 if weights.get(k, 0) >= 0.25 else 3.0
        cov = min(float(scores.get(k, 3.0)) / target, 1.0); parts[k] = dict(weight=w, target=target, coverage=cov); num += w * cov; den += w
    return dict(value=round(100 * num / den), parts=parts)


def role_market_view(art: dict, results: dict, role: str) -> dict:
    info = role_info(art, role)
    base = {"Data Scientist": "Data Scientist", "Data Analyst": "Data Analyst", "Data Engineer": "Data Engineer"}.get(role)
    lad = (results.get("ladder") or {}).get(base) if base else None
    return dict(info=info, ladder=lad)
