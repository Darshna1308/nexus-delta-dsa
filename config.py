"""NEXUS DELTA — configuration, palette and provenance registry (single place for labels/sources)."""
import os

DATA_DIR = os.environ.get("NEXUS_DATA_DIR", "out")
FIG_DIR = os.environ.get("NEXUS_FIG_DIR", "figs")

BRAND = dict(product="NEXUS DELTA", tagline="Evidence-First Workforce Capability Decision Engine",
             hero=["Know what to build.", "Know what to learn.", "Know where you can thrive."],
             team="Team DSA", uni="Chandigarh University", event="Build For Bharat 2.0",
             members=["Anwesha Kar", "Darshna Parihar", "Saamyaraj Baidya"])

# palette (colour psychology): ivory workspace · deep indigo for structure/trust · muted teal for evidence · terracotta for action/attention · muted green for growth/FUND · antique gold for rare high-value insight
# key 'blue' is the ACTION accent (terracotta) for backward compatibility
C = dict(navy="#16324F", navy2="#1E3F60", navy3="#2A4E72", blue="#C87941", blue_soft="#F4E6D8", teal="#2F5D62", teal_soft="#DCE7E5", green="#5F8065", green_soft="#E3EBE2",
         gold="#D9A441", paper="#F6F3EC", card="#FBF9F4", ink="#17212B", muted="#68737D", line="#DDD5C6", amber="#B98A2E", amber_soft="#F6EBD3",
         red="#A84A32", red_soft="#F5E1DA", grey="#8A939B", indigo_soft="#E2E8EE")

CAPS = ["maths_stats", "story", "ai_ml", "coding", "big_data"]            # display order used across the app
LABEL = {"big_data": "Big Data", "maths_stats": "Maths & Statistics", "coding": "Coding", "ai_ml": "AI & ML", "story": "Dashboards & Storytelling"}
SHORT = {"big_data": "Big Data", "maths_stats": "Maths & Stats", "coding": "Coding", "ai_ml": "AI & ML", "story": "Storytelling"}
CAP_BY_LABEL = {v: k for k, v in LABEL.items()}

PAGES = ["HOME", "EVIDENCE", "CAPABILITY INTELLIGENCE", "INSIGHTS", "DECISION", "CAREER INTELLIGENCE", "JD SCANNER", "WORK DNA", "CULTURE", "ABOUT"]
TOP_N = 5   # first five in the top bar, the rest under MORE
PAGE_SLUG = {"home": "HOME", "capability": "CAPABILITY INTELLIGENCE", "career": "CAREER INTELLIGENCE", "scanner": "JD SCANNER", "workdna": "WORK DNA", "insights": "INSIGHTS", "decision": "DECISION", "overview": "HOME", "culture": "CULTURE", "evidence": "EVIDENCE", "about": "ABOUT"}

EVIDENCE_LABELS = {  # label -> (meaning, colour)
    "OBSERVED": ("Counted or measured directly in the supplied data.", C["teal"]),
    "DERIVED": ("Computed from observed data by a documented method.", C["blue"]),
    "INFERRED": ("A model-based what-if or association; not causal.", C["amber"]),
    "ASSUMED": ("A stated assumption.", C["grey"]),
    "PROPOSED": ("A product design not validated against data.", C["red"]),
    "SIMULATED": ("Illustrative values created for the demo.", C["grey"]),
}

NB = {"01": "01_data_exploration_cleaning", "02": "02_internal_evidence_JDS_SDS", "03": "03_T1_high_hike_model", "04": "04_market_salary_band_model",
      "05": "05_T2_JD_scanner_salary_band", "06": "06_headroom_career_decision_engine", "07": "07_app_role_profiles"}

# provenance registry: key -> where a number comes from (shown by the badge popovers and the Evidence page)
PROV = {
    "jds_effects": dict(label="DERIVED", file="JDS_Skill_Traits.xlsx", nb="02", key="jds_effects", method="Mann–Whitney U + Cliff's δ, 2,000-bootstrap 95% CI, Holm correction", limit="One company, n = 139; association only; 25 rows carry conflicting labels."),
    "jds_ceiling": dict(label="OBSERVED", file="JDS_Skill_Traits.xlsx", nb="02", key="jds_ceiling", method="Share of juniors scoring exactly 5.0", limit="Ceiling is not the same as mastery."),
    "market_or": dict(label="DERIVED", file="Analytics_Jobs.csv", nb="04", key="market_or", method="Ordinal logit of 6 salary bands; primary and wide taxonomies; 6 specifications", limit="Posting-level banded salary; truncated skill text (87%); association, not causation."),
    "story_decomp": dict(label="DERIVED", file="Analytics_Jobs.csv", nb="04", key="story_decomp", method="Ordinal logit with storytelling split into visualisation tools vs MIS/reporting-only", limit="MIS-only is also a role-level proxy."),
    "headroom": dict(label="INFERRED", file="JDS_Skill_Traits.xlsx", nb="06", key="headroom", method="E_k = mean change in P(high hike) for a +0.5 step (capped at 5.0) from an L2 logistic; 1,000 bootstrap refits", limit="What-if association; not a causal training effect."),
    "headroom_pct": dict(label="OBSERVED", file="JDS_Skill_Traits.xlsx", nb="06", key="headroom.headroom", method="Share of juniors with score < 5.0", limit="Observable room only."),
    "matrix": dict(label="DERIVED", file="all four files", nb="06", key="matrix", method="Printed rule set over δ, odds ratios and headroom", limit="Rules, not a weighted score; thresholds are stated in the Evidence page."),
    "decision": dict(label="DERIVED", file="JDS_Skill_Traits.xlsx", nb="06", key="decision", method="Winner must beat the next funded lever in ≥ 80% of 1,000 bootstrap refits", limit="Statistical tie is declared otherwise."),
    "t1_models": dict(label="DERIVED", file="JDS_Skill_Traits.xlsx", nb="03", key="t1_models", method="7-model zoo, StratifiedGroupKFold × 10–20 repeats, 300-shuffle permutation", limit="Single company; does not generalise without new outcome data."),
    "t2_models": dict(label="DERIVED", file="Analytics_Jobs.csv", nb="05", key="t2_models", method="7-model zoo, GroupKFold by designation, permutation test, paired bootstrap", limit="Exact-band accuracy < 50%: show a distribution, never a salary."),
    "ladder": dict(label="OBSERVED", file="DataScience_Jobs.csv", nb="06", key="ladder", method="Company-paired senior/junior median ratio, Wilcoxon signed-rank, bootstrap CI", limit="No dates: structural comparison, not a time trend."),
    "role_profiles": dict(label="DERIVED", file="Analytics_Jobs.csv", nb="07", key="role_profiles", method="Capability prevalence (skills + description text only) and salary-band shares among postings whose title matches the role", limit="Truncated skill lists lower prevalence; Analytics Consultant sample is small (n = 140)."),
    "bharat": dict(label="OBSERVED", file="Analytics_Jobs.csv", nb="04", key="bharat", method="Descriptive shares by location tier", limit="Tier-2/3 sample is small (n = 407 DS&A postings)."),
    "cleaning": dict(label="OBSERVED", file="Analytics_Jobs.csv", nb="01", key="cleaning", method="Row reconciliation log", limit="Regex tiers/seniority are rule-based."),
    "id_overlap": dict(label="OBSERVED", file="all four files", nb="01", key="id_overlap", method="Identifier overlap audit", limit="Overlaps are numerical coincidences — no valid row-level join."),
    "sds": dict(label="OBSERVED", file="SDS_Personality_Traits.xlsx", nb="02", key="sds", method="Cliff's δ per trait; grouped-CV logistic", limit="Near-perfect separability; cohort context only, never an individual score and NOT an EQ score."),
    "scanner_tags": dict(label="DERIVED", file="Analytics_Jobs.csv", nb="01", key="taxonomy.json", method="cap-tax-v2.0 regex taxonomy applied to pasted/scanned text", limit="Regex taxonomy not hand-audited; keywords can over-match."),
    "scanner_band": dict(label="DERIVED", file="Analytics_Jobs.csv", nb="05", key="t2_models / jd_scanner_m2.joblib", method="TF-IDF + structured logistic regression (selected T2 model)", limit="≈ 44% exact-band accuracy, ≈ 85% within ±1 band: a distribution, not a salary."),
    "work_signals": dict(label="PROPOSED", file="(none — keyword lexicon)", nb="—", key="jd_scanner.WORK_LEXICON", method="Deterministic keyword cues in the JD text", limit="Not validated; absence of a cue means 'no signal', not 'low demand'."),
    "work_dna": dict(label="PROPOSED", file="(none — self-assessment)", nb="—", key="work_dna.py", method="15-item self-assessment; printed friction rules", limit="Not validated; not a medical, clinical or hiring instrument; not a prediction."),
    "role_dna": dict(label="SIMULATED", file="(illustrative)", nb="—", key="work_dna.ROLE_PROFILES", method="Hand-written illustrative profiles", limit="NOT company measurements. Edit them for your own role."),
    "technical_fit": dict(label="DERIVED", file="Analytics_Jobs.csv", nb="07", key="career.technical_fit", method="Coverage of required capability levels weighted by observed role demand", limit="A readiness index from self-entered scores; not a prediction of success."),
    "eq": dict(label="PROPOSED", file="(none — self-assessment)", nb="—", key="eq.py", method="15-item optional self-assessment", limit="Indicative self-assessment — not clinical or validated; never used in fit, hiring or rejection."),
}
