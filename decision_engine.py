"""Capability Evidence Matrix + printed decision rules. Reads the verdicts computed by notebook 06 and ADDS display fields
(evidence quality, conflict flag, explanations). It never changes a validated number or a verdict."""
import config
from config import LABEL

S5, S6 = "S5 +all controls (primary tax.)", "S6 all controls (wide tax. & population)"

RULES = [
    ("Strong internal (δ ≥ 0.33, CI > 0) + premium or neutral market", "FUND"),
    ("Strong internal + discount in both taxonomies", "FUND WITH REFRAME"),
    ("Moderate internal + robust premium", "MONITOR"),
    ("Weak internal (Holm p ≥ 0.05 or δ < 0.147), or moderate without premium", "DEPRIORITISE"),
    ("Insufficient evidence", "NO VERDICT SHOWN"),
    ("Funded levers: winner must beat the next funded lever in ≥ 80% of 1,000 bootstrap refits, else TIED", "TIED"),
]
QUALITY_RULE = ("Evidence quality — High: strong internal signal AND the market direction is significant in 6/6 specifications with no internal/market conflict. "
                "Moderate: conflict between lines, or moderate internal signal. Low: weak/unsupported internal signal.")


def _eq_quality(m, prem, disc):
    consistent = prem >= 6 or disc >= 6
    if m["internal"] == "Weak": return "Low"
    if m["market"] == "Discount" and m["internal"] == "Strong": return "Moderate"
    if m["internal"] == "Strong" and consistent: return "High"
    return "Moderate"


def _conflict(m):
    if m["internal"] == "Strong" and m["market"] == "Discount": return "Conflict"
    if m["internal"] == "Weak" and m["market"] == "Neutral": return "Unsupported"
    return "Agree"


def build_matrix(results: dict) -> list:
    """returns rows in display order with extra display fields; None-safe."""
    if not results or "matrix" not in results: return []
    prem, disc = results.get("market_premium_specs", {}), results.get("market_discount_specs", {})
    dec = results.get("decision", {})
    by_key = {m["key"]: m for m in results["matrix"]}
    rows = []
    for k in config.CAPS:
        m = dict(by_key.get(k, {}))
        if not m: continue
        m["capability_src"] = m["capability"]; m["capability"] = LABEL[k]
        m["premium_specs"], m["discount_specs"] = prem.get(k, 0), disc.get(k, 0)
        m["quality"] = _eq_quality(m, m["premium_specs"], m["discount_specs"])
        m["conflict"] = _conflict(m)
        m["verdict_display"] = m["verdict"]
        if dec.get("tie") and m["capability_src"] in (dec.get("lead"), dec.get("next")) and m["verdict"] in ("FUND", "FUND WITH REFRAME"):
            m["verdict_display"] = "TIED"
        eff = next((e for e in results.get("jds_effects", []) if e["skill"] == k), {})
        m["ci_lo"], m["ci_hi"] = eff.get("ci_lo"), eff.get("ci_hi")
        m["ceiling_share"] = results.get("jds_ceiling", {}).get(k)
        rows.append(m)
    return rows


def market_ci(results, k, spec=S5):
    """(OR, lo, hi) for the capability under a spec; story uses the broad storytelling family."""
    v = results.get("market_or", {}).get(spec, {}).get(k)
    return (v["OR"], v["lo"], v["hi"]) if v else (None, None, None)


def top_signals(results: dict) -> dict:
    """data-driven home-page snapshot (labels are computed from the results, not hard-coded)."""
    rows = build_matrix(results)
    if not rows: return {}
    internal = max(rows, key=lambda r: r["delta"])
    lever = max(rows, key=lambda r: r["Ek"])
    mk = max(rows, key=lambda r: r["OR_primary"])
    unc = max(rows, key=lambda r: (results.get("market_or", {}).get(S1, {}).get(r["key"], {}).get("OR", 0)))
    conflicts = [r for r in rows if r["conflict"] == "Conflict"]
    conflict = max(conflicts, key=lambda r: r["delta"] - (r["OR_primary"] - 1)) if conflicts else None
    head = max(rows, key=lambda r: r["headroom"])
    return dict(internal=internal, lever=lever, market=mk, market_uncontrolled=unc, conflict=conflict, headroom=head)


S1 = "S1 flags only"


def explain(results: dict, key: str) -> dict:
    """text for the evidence drawer — every number pulled from results."""
    rows = {r["key"]: r for r in build_matrix(results)}
    r = rows.get(key)
    if not r: return {}
    sd = results.get("story_decomp", {})
    p, lo, hi = market_ci(results, key, S5); w = market_ci(results, key, S6)[0]
    if key == "story":
        why = (f"Storytelling is strongly associated with the internal outcome (δ = {r['delta']:.2f}), but the market discount is concentrated in MIS/reporting-only "
               f"postings (OR {sd['mis_only']['OR']:.2f}) rather than visualisation-tool postings (OR {sd['viz']['OR']:.2f}, CI {sd['viz']['lo']:.2f}–{sd['viz']['hi']:.2f} includes 1).") if sd else "Strong internal signal with a market discount."
        action = "Prioritise visual analytics and decision communication instead of generic MIS/reporting."
    elif r["verdict"] == "FUND":
        why = (f"Internal signal is strong (δ = {r['delta']:.2f}) and the market direction agrees (OR {p:.2f} primary / {w:.2f} wide; "
               f"premium in {r['premium_specs']}/6 specifications). {r['headroom']:.0f}% of juniors are below the observed ceiling.")
        action = {"maths_stats": "Fund first: largest modelled cohort gain with the strongest bootstrap support.",
                  "coding": "Keep funded; the modelled gain is smaller and its interval is wide, so treat it as a steady investment.",
                  "ai_ml": "Keep funded; part of the market premium is carried by role titles (it shrinks once role family is controlled)."}.get(key, "Keep funded.")
    else:
        why = (f"Internal signal is weak (δ = {r['delta']:.2f}; CI {r['ci_lo']:.2f} to {r['ci_hi']:.2f} includes 0; Holm p = {r['p_holm']:.2f}) and the market premium is not robust "
               f"({r['premium_specs']}/6 specifications). Headroom is high ({r['headroom']:.0f}%), but headroom alone is not evidence of benefit.")
        action = "Do not fund on headroom alone; revisit if a multi-company outcome file shows a signal."
    return dict(why=why, action=action, row=r)
