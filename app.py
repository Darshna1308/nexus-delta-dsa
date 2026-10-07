"""NEXUS DELTA — Evidence-First Workforce Capability Decision Engine. Team DSA · Chandigarh University · Build For Bharat 2.0
Run:  streamlit run app.py     (offline: reads out/results.json, out/taxonomy.json, out/app_artifacts.json, out/jd_scanner_m2.joblib)"""
import streamlit as st
st.set_page_config(page_title="NEXUS DELTA — Evidence-First Workforce Capability Decision Engine", page_icon="◆", layout="wide", initial_sidebar_state="collapsed")

import config, ui, charts, data, auth, account_ui as AC, culture as CU
import decision_engine as de, career, jd_scanner as J, work_dna as W
from config import C, LABEL, SHORT, CAPS, PAGES, PROV

S = st.session_state

SAMPLE_JDS = {  # SIMULATED: written for the demo, not real postings
    "Senior Data Scientist — startup (sample)": "Senior Data Scientist\nWe are a fast-paced Bengaluru startup. You will own machine learning models end-to-end, work with cross-functional stakeholders and present insights to leadership. "
        "5-8 years experience. Python, SQL, machine learning, NLP, Tableau, statistics. Tight deadlines and changing priorities are normal; you will be a self-starter who can figure things out with little supervision.",
    "Data Analyst — enterprise reporting (sample)": "Data Analyst - MIS & Reporting\nMumbai. 2-4 years experience. Prepare daily MIS reports in Excel and SQL, follow documented processes and compliance checklists, maintain dashboards in Power BI, "
        "coordinate with the finance team and communicate findings clearly. Strong attention to detail; defined processes and clear roadmap provided.",
    "Analytics Consultant — client-facing (sample)": "Analytics Consultant\nGurugram. 4-7 years experience. Work with client stakeholders to frame business problems, build statistical models and forecasting in Python and R, present recommendations to client leadership, "
        "collaborate in cross-functional teams, travel up to 30%. Fast-paced delivery with tight deadlines; excellent written and verbal communication.",
}
DEMO_ANSWERS = {0: 4, 1: 4, 2: 4, 3: 5, 4: 4, 5: 4, 6: 4, 7: 3, 8: 4, 9: 3, 10: 4, 11: 5, 12: 3, 13: 3, 14: 4}   # SIMULATED persona for the demo only
DEMO_SCORES = {"ai_ml": 4, "coding": 4, "maths_stats": 3, "big_data": 3, "story": 4}
ROLE_PROFILE_TO_CAREER = {"Startup Data Scientist": "Data Scientist", "Enterprise Data Scientist": "Data Scientist", "Research Data Scientist": "Data Scientist", "Analytics Consultant": "Analytics Consultant"}


# ============================================================================ state & navigation
def init_state():
    if "page" not in S:
        qp = st.query_params
        S.page = config.PAGE_SLUG.get(str(qp.get("page", "home")).lower(), "HOME")
        S.demo_on = False; S.demo_step = 0; S._boot_demo = int(qp.get("demo_step", 0) or 0) if str(qp.get("demo", "")) == "1" else None
        if str(qp.get("demo", "")) == "1": S.guest = True   # demo mode needs no account
    S.setdefault("demo_on", False); S.setdefault("demo_step", 0); S.setdefault("cap_sel", "story"); S.setdefault("role", "Data Scientist")
    for k in CAPS: S.setdefault(f"score_{k}", 3)
    S.setdefault("jd_text", ""); S.setdefault("jd_result", None); S.setdefault("dna_stage", "intro"); S.setdefault("dna_q", 0); S.setdefault("dna_ans", {})
    S.setdefault("dna_role", "Startup Data Scientist"); S.setdefault("dna_tab", "YOUR FIT"); S.setdefault("eq_stage", "offer"); S.setdefault("hear_text", ""); S.setdefault("hear_conf", 1.0)
    S.setdefault("dna_consent", False)
    if S.get("_boot_demo") is not None:
        step = S._boot_demo; S._boot_demo = None; S.demo_on = True; demo_apply(max(step - 1, 0))


def go(page, **kw):
    S.page = page
    for k, v in kw.items(): S[k] = v
    st.query_params["page"] = {v: k for k, v in config.PAGE_SLUG.items()}[page]


def open_cap(k): go("CAPABILITY INTELLIGENCE", cap_sel=k)
def scores(): return {k: float(S.get(f"score_{k}", 3) or 3) for k in CAPS}


# ============================================================================ DEMO MODE (12 steps)
DEMO_STEPS = [
    ("HOME", "Open NEXUS DELTA", "One engine, two lenses: what should an organisation fund — and what should I learn."),
    ("HOME", "The conflict", "“Storytelling is the strongest internal separator, but the market signal conflicts.”"),
    ("CAPABILITY INTELLIGENCE", "Open the evidence drawer", "Every number behind FUND WITH REFRAME — δ, odds ratios, headroom — with provenance badges."),
    ("CAREER INTELLIGENCE", "Switch to student mode", "Same evidence engine, different question: what should I develop next?"),
    ("CAREER INTELLIGENCE", "Select Data Scientist", "Development priorities from market evidence + your entered levels — never a salary prediction."),
    ("JD SCANNER", "Scan a role", "A job description is decoded locally: capabilities, experience, salary-band distribution."),
    ("JD SCANNER", "Technical requirements & market evidence", "Tags from the taxonomy, a probability distribution (never a fake exact salary), and the caveat."),
    ("WORK DNA", "Open Work DNA", "Will the way this role works fit the way you work? (Demo persona is SIMULATED.)"),
    ("WORK DNA", "Your Work DNA vs Role Work DNA", "The role profile is ILLUSTRATIVE — not a company measurement."),
    ("WORK DNA", "Technical fit · work-style fit · sustainability friction", "Three honest numbers — no hire/reject, no burnout prediction."),
    ("WORK DNA", "What should I ask before accepting?", "Friction becomes concrete questions for the employer."),
    ("HOME", "Close", "NEXUS DELTA doesn't just help you qualify for a role. It helps you decide whether the role is right for you."),
]


def demo_apply(i):
    i = max(0, min(i, len(DEMO_STEPS) - 1)); S.demo_step = i; page = DEMO_STEPS[i][0]; go(page)
    if i == 2: S.cap_sel = "story"
    if i >= 4:
        S.role = "Data Scientist"
        for k, v in DEMO_SCORES.items(): S[f"score_{k}"] = v
    if i >= 5 and not S.jd_result:
        S.jd_text = list(SAMPLE_JDS.values())[0]; do_scan(demo=True)
    if i >= 7:
        S.dna_ans = dict(DEMO_ANSWERS); S.dna_stage = "result"; S.dna_consent = True; S.dna_role = "Startup Data Scientist"; S.dna_tab = "YOUR FIT"


def demo_start(): S.demo_on = True; demo_apply(0)
def demo_exit(): S.demo_on = False


def demo_bar():
    i = S.demo_step; page, title, cap = DEMO_STEPS[i]
    with st.container(key="demobar"):
        c = st.columns([7.2, 0.9, 0.9, 0.8], vertical_alignment="center")
        with c[0]: ui.md(f"<div style='color:#fff;font-size:12.5px;line-height:1.35'><b style='letter-spacing:.1em'>DEMO MODE · STEP {i+1:02d} / {len(DEMO_STEPS)}</b> &nbsp;—&nbsp; <b>{ui.esc(title)}</b><br><span style='opacity:.92'>{ui.esc(cap)}</span></div>")
        with c[1]: st.button("◀ BACK", key="demo_back", on_click=demo_apply, args=(i - 1,), disabled=i == 0, width="stretch")
        with c[2]: st.button("NEXT ▶", key="demo_next", on_click=demo_apply, args=(i + 1,), disabled=i == len(DEMO_STEPS) - 1, width="stretch")
        with c[3]: st.button("EXIT", key="demo_exit", on_click=demo_exit, width="stretch")


# ============================================================================ reusable evidence card (used by Capability page, Hear, Home tiles)
def evidence_card(b, k, compact=False):
    rows = {r["key"]: r for r in de.build_matrix(b.results)}; r = rows.get(k)
    if not r: ui.err("No evidence available for that capability."); return
    ex = de.explain(b.results, k)
    ui.md(f"<div class='nd-label'>CAPABILITY</div><div class='nd-val s'>{ui.esc(LABEL[k]).upper()}</div>")
    c = st.columns(4)
    with c[0]: ui.stat("INTERNAL SIGNAL", ui.signal_chip(r["internal"]), f"δ = {r['delta']:.2f}" + (f" [{r['ci_lo']:.2f}, {r['ci_hi']:.2f}]" if r.get("ci_lo") is not None else ""))
    with c[1]: ui.stat("MARKET SIGNAL", ui.signal_chip(r["market"]), f"OR {r['OR_primary']:.2f} / {r['OR_wide']:.2f}")
    with c[2]: ui.stat("HEADROOM", f"{r['headroom']:.0f}%", "below the observed ceiling")
    with c[3]: ui.stat("EVIDENCE QUALITY", ui.signal_chip(r["quality"]), f"{r['premium_specs']}/6 premium specs")
    ui.md(f"<div style='margin-top:10px'>{ui.verdict_chip(r['verdict_display'])}</div><div style='font-size:13.5px;line-height:1.5;margin-top:8px'>{ui.esc(ex['why'])}</div><div class='nd-action'><b>ACTION</b>{ui.esc(ex['action'])}</div>")


# ============================================================================ HOME
def page_home(b):
    ui.hero("EVIDENCE-FIRST WORKFORCE CAPABILITY DECISION ENGINE",
            "Know what to build.<br>Know what to learn.<br><em>Know where you can thrive.</em>",
            "NEXUS DELTA connects market demand, workforce evidence, capability headroom and work-style fit into one transparent decision layer.")
    with st.container(key="body"):
        if not b.ok_results: ui.err(f"Evidence data unavailable: {b.errors.get('results', 'results.json missing')}. Run notebooks 01–07 to regenerate out/results.json."); ui.footer(); return
        cs = st.columns(3, gap="medium")
        paths = [("01 — ORGANISATION", "What capability should we develop?", "Evidence matrix of five capabilities with an auditable verdict.", "CAPABILITY INTELLIGENCE", "OPEN CAPABILITY INTELLIGENCE ›"),
                 ("02 — STUDENT / PROFESSIONAL", "What should I develop next?", "Priorities from market evidence, role demand and your own levels.", "CAREER INTELLIGENCE", "OPEN CAREER INTELLIGENCE ›"),
                 ("03 — WORK DNA", "Will this work environment fit me?", "Work-style fit and friction, with the questions to ask the employer.", "WORK DNA", "OPEN WORK DNA ›")]
        for col, (kick, q, sub, page, cta) in zip(cs, paths):
            with col, st.container(key=f"card_path_{page[:4]}"):
                ui.md(f"<div class='nd-label' style='color:{C['blue']}'>{kick}</div><div class='nd-val s' style='margin:4px 0 6px 0'>{ui.esc(q)}</div><div class='nd-sub' style='min-height:34px'>{ui.esc(sub)}</div>")
                st.button(cta, key=f"path_{page[:4]}", on_click=go, args=(page,), type="primary" if page == "CAPABILITY INTELLIGENCE" else "secondary")
        ui.md(f"<div class='nd-label' style='margin:22px 0 8px 0'>INTELLIGENCE SNAPSHOT — computed from results.json · click to open the evidence</div>")
        sg = de.top_signals(b.results); tiles = []
        if sg:
            tiles = [("STRONGEST INTERNAL SEPARATOR", LABEL[sg["internal"]["key"]], f"Cliff's δ {sg['internal']['delta']:.2f} · JDS n = 139", sg["internal"]["key"], "jds_effects"),
                     ("TOP COHORT LEVER (MODELLED)", LABEL[sg["lever"]["key"]], f"+{sg['lever']['Ek']:.1f} pp P(high hike) per +0.5 step", sg["lever"]["key"], "headroom"),
                     ("STRONGEST MARKET SIGNAL", LABEL[sg["market"]["key"]], f"OR {sg['market']['OR_primary']:.2f} with controls · {SHORT[sg['market_uncontrolled']['key']]} is higher before role controls", sg["market"]["key"], "market_or"),
                     ("BIGGEST EVIDENCE CONFLICT", LABEL[sg["conflict"]["key"]] if sg["conflict"] else "None", (f"internal δ {sg['conflict']['delta']:.2f} vs market OR {sg['conflict']['OR_primary']:.2f}" if sg["conflict"] else ""), sg["conflict"]["key"] if sg["conflict"] else "story", "story_decomp"),
                     ("HIGHEST HEADROOM", LABEL[sg["headroom"]["key"]], f"{sg['headroom']['headroom']:.0f}% below ceiling — but {sg['headroom']['verdict'].lower()}", sg["headroom"]["key"], "headroom_pct")]
        for col, (lab, val, sub, k, pk) in zip(st.columns(len(tiles) or 1, gap="small"), tiles):
            with col, st.container(key=f"card_tile_{lab[:6]}{k}"):
                ui.md(f"<div class='nd-label'>{lab}</div><div class='nd-val s' style='min-height:54px'>{ui.esc(val)}</div><div class='nd-sub' style='min-height:50px'>{ui.esc(sub)}</div>")
                c1, c2 = st.columns([1.5, 1.2])
                with c1, st.container(key=f"tile_{lab[:6]}{k}"): st.button("OPEN EVIDENCE ›", key=f"open_{lab[:6]}{k}", on_click=open_cap, args=(k,))
                with c2: ui.prov(pk, f"home_{lab[:6]}")
        ui.md(f"<div class='nd-label' style='margin:24px 0 8px 0'>THE LOOP — one evidence engine behind both lenses</div>")
        steps = ["MARKET DEMAND", "CAPABILITY EVIDENCE", "INTERNAL SIGNAL", "MARKET SIGNAL", "HEADROOM", "CAREER CONTEXT", "CONFLICT DETECTION", "DEVELOPMENT DECISION", "ROLE / WORK-STYLE FIT", "ACTION"]
        ui.md("<div style='display:flex;flex-wrap:wrap;gap:6px;align-items:center'>" + " <span style='color:#8D99AE'>→</span> ".join(ui.chip(s, "ink" if i in (7, 9) else "grey") for i, s in enumerate(steps)) + "</div>")
        c = st.columns([1, 1, 3])
        with c[0]: st.button("▶ START 3-MIN DEMO", key="demo_start", on_click=demo_start, type="primary")
        with c[1]: st.button("HOW WE PROTECT YOU", key="home_protect", on_click=go, args=("ABOUT",))
        ui.footer()


# ============================================================================ CAPABILITY INTELLIGENCE
def page_capability(b):
    with st.container(key="body"):
        ui.header("What should we invest in next?", "One evidence matrix, five capabilities. Click a capability to open the evidence behind its verdict.", "CAPABILITY INTELLIGENCE · ORGANISATION LENS")
        if not b.ok_results: ui.err(f"Evidence data unavailable ({b.errors.get('results', 'results.json missing')}). Run notebooks 01–07."); ui.footer(); return
        rows = de.build_matrix(b.results); dec = b.results.get("decision", {})
        order = {"FUND": 0, "TIED": 0, "FUND WITH REFRAME": 1, "MONITOR": 2, "DEPRIORITISE": 3}
        rows.sort(key=lambda r: (order.get(r["verdict_display"], 4), -r["Ek"]))
        if dec:
            ui.md(f"<div style='display:flex;gap:10px;align-items:center;margin-bottom:10px'><span style='font-size:13.5px'><b>Lead lever: {ui.esc(dec.get('lead',''))}</b> — beats {ui.esc(dec.get('next',''))} in {dec.get('p_beat',0):.0%} of 1,000 bootstrap refits → {'statistical TIE' if dec.get('tie') else 'clear winner (≥ 80% rule)'}.</span></div>")
        left, right = st.columns([1.75, 1], gap="large")
        with left:
            W_ = [2.0, 1.35, 1.5, 1.25, 1.1, 1.35, 2.15]; hdr = st.columns(W_)
            for col, t in zip(hdr, ["CAPABILITY", "INTERNAL SIGNAL", "MARKET SIGNAL", "HEADROOM", "EVIDENCE QUALITY", "CONFLICT", "VERDICT"]): col.markdown(f"<div class='nd-label' style='border-bottom:1.5px solid {C['ink']};padding-bottom:5px'>{t}</div>", unsafe_allow_html=True)
            for r in rows:
                with st.container(key=f"row_{r['key']}"):
                    c = st.columns(W_, vertical_alignment="center")
                    with c[0], st.container(key=f"caplink_{r['key']}"): st.button(LABEL[r["key"]], key=f"cap_{r['key']}", on_click=lambda k=r["key"]: S.__setitem__("cap_sel", k))
                    with c[1]: ui.md(f"{ui.signal_chip(r['internal'])}<div class='nd-sub'>δ {r['delta']:.2f}</div>")
                    with c[2]: ui.md(f"{ui.signal_chip(r['market'])}<div class='nd-sub'>OR {r['OR_primary']:.2f} · {r['OR_wide']:.2f}</div>")
                    with c[3]: ui.md(f"<div style='font-size:13px;font-weight:600'>{r['headroom']:.0f}%</div><div class='nd-hbar'><span style='width:{r['headroom']:.0f}%'></span></div>")
                    with c[4]: ui.md(ui.signal_chip(r["quality"]))
                    with c[5]: ui.md(ui.signal_chip(r["conflict"]))
                    with c[6]: ui.md(ui.verdict_chip(r["verdict_display"]))
            ui.md(f"<div class='nd-sub' style='margin-top:8px'>δ = Cliff's delta (internal); OR = market odds ratio, primary · wide taxonomy; headroom = share of juniors below the 5.0 ceiling. Rules are printed below.</div>")
            pc = st.columns([1, 6]); 
            with pc[0]: ui.prov("matrix", "cap")
        with right:
            with st.container(key="card_drawer"):
                evidence_card(b, S.cap_sel if S.cap_sel in CAPS else "story")
                k = S.cap_sel if S.cap_sel in CAPS else "story"; r0 = next(x for x in rows if x["key"] == k)
                hr = b.results.get("headroom", {}); i = hr.get("skills", []).index(k) if k in hr.get("skills", []) else None
                if i is not None: ui.md(f"<div class='nd-note'>Modelled cohort gain E_k = <b>{hr['Ek'][i]:.2f} pp</b> [{hr['ci_lo'][i]:.2f}, {hr['ci_hi'][i]:.2f}] · P(top lever) {hr['ptop'][i]:.2f}. A what-if association, not a causal training effect.</div>")
                pc = st.columns([1, 1, 1, 2])
                with pc[0]: ui.prov("jds_effects", "drawer")
                with pc[1]: ui.prov("market_or", "drawer")
                with pc[2]: ui.prov("headroom", "drawer")
        with st.expander("EVIDENCE-CONFLICT MAP & MODELLED COHORT GAINS", expanded=False):
            c1, c2 = st.columns(2)
            with c1: ui.md("<div class='nd-label'>INTERNAL vs MARKET (bubble = headroom)</div>"); st.plotly_chart(charts.conflict_map(rows, S.cap_sel), width="stretch", config={"displayModeBar": False}, key="pc_conflict")
            with c2: ui.md("<div class='nd-label'>MODELLED COHORT GAIN E_k</div>"); st.plotly_chart(charts.ek_bars(rows), width="stretch", config={"displayModeBar": False}, key="pc_ek")
        with st.expander("HOW VERDICTS ARE DECIDED (printed rules)", expanded=False):
            ui.md("<table class='nd-tbl'><tr><th>Condition</th><th>Verdict</th></tr>" + "".join(f"<tr><td>{ui.esc(c)}</td><td>{ui.verdict_chip(v)}</td></tr>" for c, v in de.RULES) + "</table>")
            ui.note(ui.esc(de.QUALITY_RULE)); ui.note("A human makes the decision; NEXUS DELTA never auto-funds or auto-rejects. Ties are shown as TIED and the market odds ratio is the tie-breaker.")
        ui.footer()


# ============================================================================ CAREER INTELLIGENCE
def page_career(b):
    with st.container(key="body"):
        ui.header("I want to become…", "Choose a target role, set your current levels, and get an evidence-based development order. This is a development recommendation — not a salary prediction.", "CAREER INTELLIGENCE · STUDENT / PROFESSIONAL LENS")
        if not b.ok_results: ui.err("Evidence data unavailable. Run notebooks 01–07."); ui.footer(); return
        role = st.segmented_control("Target role", career.ROLES, key="role", required=True, label_visibility="collapsed") or S.role
        art = b.artifacts
        if not b.ok_roles: ui.warn("Role demand data (app_artifacts.json) is missing — priorities use market evidence only. Run notebook 07 to restore role demand.")
        left, right = st.columns([1, 1.25], gap="large")
        sc = scores(); info = career.role_info(art, role); dem = info.get("capability_share", {})
        with left, st.container(key="card_profile"):
            ui.md("<div class='nd-label'>MY CURRENT CAPABILITIES</div>")
            target = {k: (4.0 if dem.get(k, 0) >= 0.25 else 3.0) for k in CAPS}
            st.plotly_chart(charts.capability_radar(sc, target), width="stretch", config={"displayModeBar": False}, key="career_radar")
            ui.md("<div class='nd-sub' style='margin:-6px 0 6px 0'>Dotted line = target level used in the readiness index (4 where ≥ 25% of the role's postings ask for it, otherwise 3).</div>")
            for k in ["ai_ml", "coding", "maths_stats", "big_data", "story"]:
                c = st.columns([1.5, 2.2], vertical_alignment="center")
                c[0].markdown(f"<div style='font-size:13px;font-weight:600'>{LABEL[k]}</div><div class='nd-sub'>role asks: {('%d%%' % round(100*dem[k])) if k in dem else '—'}</div>", unsafe_allow_html=True)
                with c[1]: st.segmented_control(LABEL[k], [1, 2, 3, 4, 5], key=f"score_{k}", required=True, label_visibility="collapsed")
            ui.md("<div class='nd-sub'>Levels: 1 = beginner · 3 = working · 5 = expert. These are your own entries (not measured).</div>")
        with right:
            tf = career.technical_fit(sc, art, role) if b.ok_roles else dict(value=None)
            c = st.columns([1, 1, 1.3])
            with c[0]: ui.stat("TECHNICAL READINESS", f"{tf['value']}%" if tf["value"] is not None else "—", "coverage of role-required levels")
            with c[1]: ui.stat("POSTINGS ANALYSED", f"{info.get('n_postings','—')}", f"{role}" + (" · small sample" if info.get("small_sample") else ""))
            with c[2]: ui.prov("technical_fit", "career"); ui.prov("role_profiles", "career")
            ui.md("<div class='nd-label' style='margin-top:10px'>YOUR DEVELOPMENT PRIORITY</div>")
            for rank, p in enumerate(career.priority_plan(b.results, art, role, sc), 1):
                with st.container(key=f"card_pr_{p['key']}"):
                    ui.md(f"<div style='display:flex;gap:10px;align-items:center;flex-wrap:wrap'><span class='nd-val s' style='font-size:20px'>{rank}. {ui.esc(p['capability'])}</span>{ui.chip(p['tier'], ui.TIER_KIND[p['tier']])}<span class='nd-sub'>you {p['your_score']:.0f}/5 · gap {p['gap']:.1f}</span></div>"
                          f"<div style='font-size:13px;margin:6px 0 8px 0'><b>WHY</b> &nbsp;{ui.esc(p['why'])}</div>"
                          f"<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px'>"
                          f"<div><div class='nd-label'>MARKET VALUE</div><div class='nd-sub' style='color:{C['ink']}'>{ui.esc(p['market_value'])}</div></div>"
                          f"<div><div class='nd-label'>HEADROOM</div><div class='nd-sub' style='color:{C['ink']}'>You: gap {p['gap']:.1f} · cohort {p['cohort_headroom']:.0f}% below ceiling</div></div>"
                          f"<div><div class='nd-label'>EVIDENCE</div><div class='nd-sub' style='color:{C['ink']}'>{ui.esc(p['evidence'])}</div></div>"
                          f"<div><div class='nd-label'>LIMITATION</div><div class='nd-sub'>{ui.esc(p['limitation'])}</div></div></div>")
            with st.expander("HOW PRIORITIES ARE ASSIGNED (printed rules)"):
                ui.md("<table class='nd-tbl'><tr><th>Tier</th><th>Rule</th></tr>" + "".join(f"<tr><td>{ui.chip(t, ui.TIER_KIND[t])}</td><td>{ui.esc(r)}</td></tr>" for t, r in career.TIER_RULES) + "</table>")
                ui.note("Order inside a tier = gap × market premium × role demand. The one-company JDS outcome model is never used to score an individual.")
        mv = career.role_market_view(art, b.results, role)
        if info:
            ui.md(f"<div class='nd-label' style='margin:18px 0 6px 0'>WHAT THE MARKET LOOKS LIKE FOR {ui.esc(role).upper()}</div>")
            c = st.columns([1.5, 1], gap="large")
            with c[0], st.container(key="card_market"):
                st.plotly_chart(charts.band_chart(info["band_share"], "of postings", C["blue"], 230), width="stretch", config={"displayModeBar": False}, key="career_band")
            with c[1], st.container(key="card_market2"):
                ui.stat("POSTINGS AT ≥ 10 LPA", f"{info['pct_ge_10LPA']:.0f}%", f"of {info['n_postings']} {role} postings (banded salary, not exact)", small=True)
                if info.get("ds_jobs"): ui.md(f"<div class='nd-note'>Data Science Jobs file: median average pay ≈ {info['ds_jobs']['median_avg_LPA']:.1f} LPA across {info['ds_jobs']['rows']} company-title rows.</div>")
                if mv["ladder"]: ui.md(f"<div class='nd-note'>Career ladder: senior pay ≈ {mv['ladder']['median_ratio']:.2f}× junior ({mv['ladder']['n']} companies paired).</div>")
                if info.get("small_sample"): ui.warn("Small sample for this role — treat the distribution as indicative.")
        ui.footer()


# ============================================================================ JD SCANNER
def do_scan(demo=False):
    b = data.get_bundle(); text = S.get("jd_text", "")
    up = S.get("jd_file")
    ext = None
    if up is not None and not demo and not text.strip():
        ext = J.extract_text(up.getvalue(), up.name); text = ext["text"]
    parsed = J.parse_jd(text, b.taxonomy)
    res = dict(parsed=parsed, probs=None, signals=None, extract=ext, ok=parsed.get("ok", False))
    if parsed.get("ok"):
        res["signals"] = J.work_signals(parsed["text"]); res["probs"] = J.salary_distribution(parsed, b.model)
        S.jd_text = parsed["text"]
    S.jd_result = res


def evidence_from_hear(b, text, conf):
    words = len(text.split())
    if words >= 20: S.jd_text = text; do_scan(); return dict(kind="scan", message="Treated as a spoken role description and scanned below.")
    it = J.parse_intent(text)
    return dict(kind="intent", intent=it)


def page_scanner(b):
    with st.container(key="body"):
        ui.header("SCAN THE ROLE", "Don't just ask what the company wants. Understand what the role actually demands.", "JD SCANNER · LOCAL · NO CLOUD API")
        mode = st.segmented_control("Input", ["PASTE TEXT", "UPLOAD PDF / IMAGE", "HEAR THIS ROLE"], key="scan_mode", default="PASTE TEXT", required=True, label_visibility="collapsed")
        with st.container(key="card_scan_in"):
            if mode == "PASTE TEXT":
                c = st.columns([3, 1], vertical_alignment="bottom")
                with c[1]:
                    pick = st.selectbox("Load a sample JD (SIMULATED)", ["—"] + list(SAMPLE_JDS), key="jd_sample", label_visibility="visible")
                    if pick != "—" and S.get("_last_sample") != pick: S.jd_text = SAMPLE_JDS[pick]; S._last_sample = pick
                with c[0]: st.text_area("Job description", key="jd_text", height=170, placeholder="Paste a job description here…")
            elif mode == "UPLOAD PDF / IMAGE":
                st.file_uploader("PDF or image", type=["pdf", "png", "jpg", "jpeg"], key="jd_file", help="Processed locally in memory; not stored.")
                if not J.ocr_available(): ui.warn("Local OCR is unavailable here — PDFs with a text layer still work; for images, paste the text instead.")
            else:
                stt = J.stt_status()
                ui.md(f"<div class='nd-label'>HEAR · local microphone → offline speech-to-text → transcript → deterministic intent parser → evidence card</div>")
                if stt["available"] and hasattr(st, "audio_input"):
                    au = st.audio_input("Speak", key="hear_audio")
                    if au is not None and S.get("_hear_done") != id(au):
                        tr = J.transcribe(au.getvalue()); S._hear_done = id(au)
                        if tr["ok"]: S.hear_text, S.hear_conf = tr["text"], tr["confidence"]
                        else: ui.warn(tr["message"])
                else:
                    ui.md(f"<div style='margin-bottom:6px'>{ui.chip('VOICE UNAVAILABLE', 'amber')} <span class='nd-sub'>{ui.esc(stt['reason'])}</span></div>")
                st.text_input("Transcript / typed question (text fallback always works)", key="hear_text", placeholder="e.g. “Should we fund Maths and Statistics?” or describe the role you heard")
                needs_confirm = S.hear_conf < J.LOW_CONF
                ok = True
                if needs_confirm: ok = st.checkbox(f"Voice confidence is low ({S.hear_conf:.0%}). I confirm the transcript above is correct.", key="hear_confirm")
                if st.button("INTERPRET", key="hear_go", type="primary", disabled=not ok):
                    S._hear_out = evidence_from_hear(b, S.hear_text, S.hear_conf) if S.hear_text.strip() else dict(kind="empty")
                out = S.get("_hear_out")
                if out:
                    if out["kind"] == "empty": ui.warn("Nothing to interpret yet — type a question or describe the role.")
                    elif out["kind"] == "intent":
                        it = out["intent"]
                        if not it["understood"]: ui.warn(it["message"])
                        else:
                            ui.md(f"<div class='nd-note'>Understood: <b>{ui.esc(it['intent'])}</b> · {ui.esc(it['message'])}</div>")
                            if it["intent"] == "capability_verdict" and b.ok_results:
                                with st.container(key="card_hear_ev"): evidence_card(b, it["slots"]["capability"])
                            st.button(f"OPEN {it['page']} ›", key="hear_open", on_click=go, args=(it["page"],), kwargs=({"role": it["slots"]["role"]} if it["slots"].get("role") else {}))
                    else: ui.md(f"<div class='nd-note'>{ui.esc(out['message'])}</div>")
            if mode != "HEAR THIS ROLE":
                if st.button("SCAN ROLE", key="scan_go", type="primary", on_click=do_scan): pass
        res = S.jd_result
        if not res: ui.footer(); return
        parsed = res["parsed"]
        if not res["ok"]:
            for w in parsed.get("warnings", []): ui.warn(w)
            if res.get("extract") and res["extract"].get("warning"): ui.warn(res["extract"]["warning"])
            ui.footer(); return
        ui.md(f"<div class='nd-label' style='margin:18px 0 6px 0;color:{C['blue']}'>ROLE DECODED</div><div class='nd-page-h' style='font-size:30px'>{ui.esc(parsed['title'])}</div>")
        for w in parsed["warnings"]: ui.warn(w)
        L, R = st.columns([1.15, 1], gap="large")
        flags = parsed["flags"]; req = [k for k in ("maths_stats", "coding", "ai_ml", "big_data", "story") if flags.get(k)]
        rows = {r["key"]: r for r in de.build_matrix(b.results)} if b.ok_results else {}
        with L, st.container(key="card_decoded"):
            ui.md("<div class='nd-label'>TECHNICAL REQUIREMENTS · CAPABILITY REQUIREMENTS</div>")
            if req:
                ui.md("<div style='display:flex;flex-wrap:wrap;gap:6px;margin:4px 0 10px 0'>" + "".join(ui.chip(LABEL[k], "blue") for k in req) + "</div>")
                ui.md("<table class='nd-tbl'><tr><th>Capability</th><th>Market signal</th><th>Verdict (org lens)</th></tr>" + "".join(
                    f"<tr><td>{ui.esc(LABEL[k])}</td><td>{ui.signal_chip(rows[k]['market']) if k in rows else '—'}</td><td>{ui.verdict_chip(rows[k]['verdict_display']) if k in rows else '—'}</td></tr>" for k in req) + "</table>")
            else: ui.md("<div class='nd-sub'>No taxonomy capabilities matched.</div>")
            ui.md(f"<div class='nd-label' style='margin-top:12px'>EXPERIENCE</div><div style='font-size:14px'>{parsed['exp_min']:.0f}–{parsed['exp_max']:.0f} years · level: {ui.esc(parsed['seniority'])} · role family: {ui.esc(parsed['role_family'])} · location tier: {ui.esc(parsed['loc_tier'])}</div>")
            pc = st.columns([1, 1, 3]); 
            with pc[0]: ui.prov("scanner_tags", "scan")
        with R, st.container(key="card_band"):
            ui.md("<div class='nd-label'>MARKET SALARY-BAND SIGNAL</div>")
            if res["probs"] is not None:
                st.plotly_chart(charts.band_chart(res["probs"], "probability", C["blue"], 230), width="stretch", config={"displayModeBar": False}, key="scan_band")
                top = int(res["probs"].argmax()); tp = float(res["probs"][top]); two = float(sorted(res["probs"])[-2] + sorted(res["probs"])[-1])
                ui.md(f"<div style='font-size:13px'>Most likely band <b>{charts.BANDS[top]} LPA</b> ({tp:.0%}); top-two bands together {two:.0%}.</div><div class='nd-note'>This is a probability distribution from a model with ≈ 44% exact-band accuracy (≈ 85% within ±1 band). It is <b>not</b> a salary prediction.</div>")
                ui.prov("scanner_band", "scan")
            else: ui.warn("Salary-band model unavailable — capability tags and work-style signals still work.")
        sig = res["signals"]; thin = {d for d, v in sig.items() if not v["signal"]}
        with st.container(key="card_signals"):
            ui.md("<div class='nd-label'>WORK-STYLE SIGNALS (keyword cues in the text · PROPOSED)</div>")
            cues = [(W.ROLE_DIM_LABEL.get(d, d), v) for d, v in sig.items() if v["signal"]]
            if cues: ui.md("<table class='nd-tbl'><tr><th>Dimension</th><th>Role demand (1–5)</th><th>Cues found</th></tr>" + "".join(f"<tr><td>{ui.esc(n)}</td><td>{v['value']:.1f}</td><td>{ui.esc(', '.join(v['up'] + ['(lowers) ' + x for x in v['down']]))}</td></tr>" for n, v in cues) + "</table>")
            else: ui.md("<div class='nd-sub'>No work-style cues found in the text.</div>")
            ui.md("<div class='nd-note'>No cue means “no signal”, not “low demand”. Dimensions without a cue are marked VERIFY in Work DNA.</div>"); ui.prov("work_signals", "scan")
        ui.md(f"<div class='nd-label' style='margin:18px 0 6px 0;color:{C['blue']}'>YOUR ROLE FIT</div>")
        sc = scores(); tf = career.technical_fit(sc, b.artifacts, required=J.required_weights(parsed))
        you = W.score_answers(S.dna_ans) if len(S.dna_ans) >= W.N_Q else None
        cmp = W.compare(you, {d: v["value"] for d, v in sig.items()}, thin) if you else None
        prem = [k for k in req if k in rows and rows[k]["market"] == "Premium"]
        c = st.columns(4, gap="medium")
        with c[0], st.container(key="card_f1"): ui.stat("TECHNICAL READINESS", f"{tf['value']}%" if tf["value"] is not None else "—", "your Career-Intelligence levels vs this JD" + (" (defaults 3/5 until you set them)" if all(v == 3 for v in sc.values()) else "")); ui.prov("technical_fit", "scan")
        with c[1], st.container(key="card_f2"): ui.stat("MARKET ALIGNMENT", f"{len(prem)} of {len(req)}" if req else "—", "required capabilities that carry a market premium"); ui.prov("market_or", "scan")
        with c[2], st.container(key="card_f3"):
            ui.stat("WORK DNA", f"{cmp['fit']}%" if cmp and cmp["fit"] is not None else "—", "work-style fit index (PROPOSED)" if cmp else "take the 3-minute assessment")
            if not cmp: st.button("OPEN WORK DNA ›", key="sc_wd", on_click=go, args=("WORK DNA",))
        with c[3], st.container(key="card_f4"):
            ui.stat("SUSTAINABILITY FRICTION", ui.chip(cmp["level"], ui.LEVEL_KIND[cmp["level"]]) if cmp else "—", "role requirements vs your self-assessment")
        st.button("COMPARE THIS ROLE WITH MY WORK DNA ›", key="sc_use", type="primary", on_click=lambda: go("WORK DNA", dna_role="From scanned JD", dna_tab="YOUR FIT"))
        ui.footer()


# ============================================================================ WORK DNA
def _bars(v, w=10): n = int(round(v * w / 5)); return "█" * n + "░" * (w - n)


def role_profile(name):
    if name in S.get("orgmap", {}): return dict(S.orgmap[name]["agg"]["job_profile"]), set()
    if name == "From scanned JD" and S.jd_result and S.jd_result["ok"]: return {d: v["value"] for d, v in S.jd_result["signals"].items()}, {d for d, v in S.jd_result["signals"].items() if not v["signal"]}
    base = W.ROLE_PROFILES.get(name, W.ROLE_PROFILES["Startup Data Scientist"])
    return {d: float(S.get(f"rd_{name}_{d}", base[d])) for d in base}, set()


def page_workdna(b):
    with st.container(key="body"):
        ui.header("Will the way this role works fit the way you work?", "Work-style fit and friction — before you commit. Not a personality test, not burnout prediction, never an auto-hire or auto-reject.", "WORK DNA · PROPOSED · SELF-ASSESSMENT")
        stage = S.dna_stage
        if stage == "intro":
            with st.container(key="card_dna_intro"):
                ui.md(f"<div class='nd-val s'>15 short questions · about 3 minutes · one question per screen</div><div class='nd-sub' style='margin:6px 0 10px 0'>Dimensions: communication, collaboration, work ethic, adaptability, autonomy, structure preference, ambiguity tolerance, pace, feedback, learning agility, social energy, recovery boundary and perspective-taking. These are <b>work-style dimensions</b>, not medical traits.</div>")
                ui.md(f"<div class='nd-note'>Your answers stay in this browser session only — nothing is stored or sent anywhere. The result compares you with a <b>role profile</b> (illustrative, scanned from a JD, or one you edit). It is {ui.chip('PROPOSED','red')} and not validated against the supplied datasets.</div>")
                st.checkbox("I consent to answering this self-assessment (optional, stays on this device).", key="dna_consent")
                st.button("START ASSESSMENT ›", key="dna_start", type="primary", disabled=not S.dna_consent, on_click=lambda: S.update(dna_stage="quiz", dna_q=0))
                st.button("SKIP TO A SAMPLE ROLE VIEW (needs answers)", key="dna_skip_info", disabled=True)
            ui.footer(); return
        if stage == "quiz":
            q = S.dna_q; dim, text, lo, hi = W.QUESTIONS[q]
            ui.md(f"<div class='nd-label'>QUESTION {q+1:02d} / {W.N_Q:02d} · {ui.esc(W.DIMS[dim]).upper()}</div><div class='nd-progress'><span style='width:{100*q/W.N_Q:.0f}%'></span></div>")
            with st.container(key="card_dna_q"):
                ui.md(f"<div class='nd-val' style='font-size:30px;max-width:900px'>{ui.esc(text)}</div>")
                cols = st.columns(5, gap="small")
                def answer(v, q=q):
                    S.dna_ans[q] = v
                    if q + 1 < W.N_Q: S.dna_q = q + 1
                    else: S.dna_stage = "result"
                for i, col in enumerate(cols, 1):
                    with col: st.button(f"{i}", key=f"dna_a_{q}_{i}", on_click=answer, args=(i,), type="primary" if S.dna_ans.get(q) == i else "secondary", width="stretch")
                ui.md(f"<div style='display:flex;justify-content:space-between;font-size:12px;color:{C['muted']};margin-top:6px'><span>1 — {ui.esc(lo)}</span><span>5 — {ui.esc(hi)}</span></div>")
            st.button("◀ BACK", key="dna_back", disabled=q == 0, on_click=lambda: S.update(dna_q=max(0, S.dna_q - 1)))
            ui.footer(); return
        # ---------------------------------------------------------------- result
        you = W.score_answers(S.dna_ans)
        if len(S.dna_ans) < W.N_Q: ui.warn(f"{W.N_Q - len(S.dna_ans)} questions unanswered — results are partial."); 
        orgmap = {f"{p['name']} · employee-reported": p for p in CU.published_orgs()}; S.orgmap = orgmap
        names = list(W.ROLE_PROFILES) + list(orgmap) + (["From scanned JD"] if S.jd_result and S.jd_result["ok"] else [])
        if S.dna_role not in names: S.dna_role = names[0]
        c = st.columns([3, 2])
        with c[0]: ui.md("<div class='nd-label'>ROLE WORK DNA</div>"); st.segmented_control("Role", names, key="dna_role", required=True, label_visibility="collapsed", width="stretch")
        with c[1]: ui.md("<div class='nd-label'>VIEW</div>"); tab = st.segmented_control("View", ["YOUR FIT", "EDIT ROLE", "ORGANISATION VIEW", "OPTIONAL EQ"], key="dna_tab", required=True, label_visibility="collapsed")
        name = S.dna_role; role, thin = role_profile(name)
        kind = "jd" if name == "From scanned JD" else ("org" if name in orgmap else "illus"); illustrative = kind == "illus"
        cmp = W.compare(you, role, thin)
        if kind == "org":
            o = orgmap[name]; badge = ui.chip(f"EMPLOYEE-REPORTED · n = {o['agg']['n']} verified employees · self-reported, not validated", "blue") + (" " + ui.chip("SIMULATED DEMO ORG", "grey") if o["simulated"] else "") + f" {ui.chip('Culture rating ' + str(o['agg']['rating']) + '/100', 'teal')}"
        else: badge = ui.chip("ILLUSTRATIVE ROLE PROFILE — not a company measurement", "grey") if illustrative else ui.chip("READ FROM SCANNED JD — keyword cues, PROPOSED", "amber")
        ui.md(f"<div style='margin:6px 0 8px 0'>{badge}</div>")
        if tab == "YOUR FIT":
            L, R = st.columns([1.2, 1], gap="large")
            with L, st.container(key="card_dna_graph"):
                ui.md("<div class='nd-label'>YOUR WORK DNA vs ROLE WORK DNA</div>")
                you_r = {d: you.get(d, 3.0) for d in W.RADAR_DIMS}; role_r = {d: role[d] for d in W.RADAR_DIMS}
                st.plotly_chart(charts.dna_radar(you_r, role_r, W.RADAR_DIMS, W.ROLE_DIM_LABEL), width="stretch", config={"displayModeBar": False}, key="dna_radar")
                ui.md("".join(f"<div class='nd-dnarow'><b>{ui.esc(r['label']).upper()}</b><div class='bar'>ROLE {_bars(r['role'])} {r['role']:.0f}<br>YOU&nbsp; {_bars(r['you'])} {r['you']:.0f}</div><div>{ui.chip(r['status'], ui.STATUS_KIND[r['status']])}</div></div>" for r in cmp["rows"]))
                ui.prov("work_dna", "graph"); ui.prov("role_dna" if illustrative else "work_signals", "graph2")
            with R:
                tf = career.technical_fit(scores(), b.artifacts, role=ROLE_PROFILE_TO_CAREER.get(name, S.get("role")), required=J.required_weights(S.jd_result["parsed"]) if (not illustrative and S.jd_result and S.jd_result["ok"]) else None) if (b.ok_roles or not illustrative) else dict(value=None)
                with st.container(key="card_dna_res"):
                    c3 = st.columns(3)
                    with c3[0]: ui.stat("TECHNICAL FIT", f"{tf['value']}%" if tf["value"] is not None else "—", "readiness from your Career levels")
                    with c3[1]: ui.stat("WORK-STYLE FIT", f"{cmp['fit']}%" if cmp["fit"] is not None else "—", "index, not a probability")
                    with c3[2]: ui.stat("SUSTAINABILITY FRICTION", ui.chip(cmp["level"], ui.LEVEL_KIND[cmp["level"]]), f"{cmp['n_high']} high · {cmp['n_watch']} watch")
                    ui.md(f"<div class='nd-label' style='margin-top:12px'>STRENGTHS</div><div style='display:flex;gap:6px;flex-wrap:wrap'>{''.join(ui.chip(s, 'teal') for s in cmp['strengths']) or '—'}</div>"
                          f"<div class='nd-label' style='margin-top:10px'>WATCH-OUTS</div><div style='display:flex;gap:6px;flex-wrap:wrap'>{''.join(ui.chip(s, 'amber') for s in cmp['watchouts']) or '—'}</div>")
                    if cmp["sentence"]: ui.md(f"<div class='nd-note' style='margin-top:10px'>{ui.esc(cmp['sentence'])}</div>")
                    ui.md(f"<div class='nd-action'><b>NEXT ACTION</b>{ui.esc(cmp['next_action'])}</div>")
                with st.container(key="card_dna_q2"):
                    ui.md("<div class='nd-label'>WORK SUSTAINABILITY · QUESTIONS TO ASK THE EMPLOYER</div>")
                    ui.md("<ol style='margin:6px 0 0 18px;font-size:13.5px;line-height:1.6'>" + "".join(f"<li>{ui.esc(q)}</li>" for q in cmp["questions"]) + "</ol>")
                    ui.md("<div class='nd-note'>Friction rules: a dimension is HIGH FRICTION when the role demand and your answer differ by more than 1.5 points (one-sided for demand-type dimensions; two-sided for structure and autonomy), WATCH above 0.75. Sustainability = HIGH if ≥ 2 high-friction dimensions or fit < 60, MODERATE if 1 high, ≥ 3 watch or fit < 75, else LOW. This is a conversation tool — not a diagnosis.</div>")
        elif tab == "EDIT ROLE":
            if kind == "org": ui.md("<div class='nd-note'>This profile is the average of what verified employees reported on the CULTURE page. It cannot be edited here.</div>")
            elif not illustrative: ui.md("<div class='nd-note'>This profile is read from the scanned JD. Re-scan to change it, or choose an illustrative role to edit.</div>")
            else:
                ui.md("<div class='nd-note'>Edit the illustrative profile to match a real role you know. Changes stay in this session.</div>")
                base = W.ROLE_PROFILES[name]; cc = st.columns(3)
                for i, d in enumerate(base):
                    with cc[i % 3]: st.slider(W.ROLE_DIM_LABEL[d], 1, 5, int(base[d]), key=f"rd_{name}_{d}")
        elif tab == "ORGANISATION VIEW":
            ui.md(f"<div class='nd-warn'><b>HUMAN DECISION-MAKER.</b> NEXUS DELTA never auto-hires or auto-rejects. Labels below are discussion prompts for an interviewer, based on a self-assessment that is PROPOSED, not validated.</div>")
            ui.md("<table class='nd-tbl'><tr><th>Dimension</th><th>Role needs</th><th>Self-assessment</th><th>Label</th></tr>" + "".join(
                f"<tr><td>{ui.esc(r['label'])}</td><td>{r['role']:.0f}</td><td>{r['you']:.0f}</td><td>{ui.chip(W.ALIGNMENT[r['status']], ui.STATUS_KIND[W.ALIGNMENT[r['status']]])}</td></tr>" for r in cmp["rows"]) + "</table>")
            ui.md("<div class='nd-sub' style='margin-top:6px'>Edit the Role Work DNA in the EDIT ROLE view. Candidate data is this session's self-assessment only.</div>")
        else:
            ui.md(f"<div class='nd-label'>OPTIONAL — EQ / PEOPLE SKILLS REPORT</div><div style='font-size:13.5px;margin:4px 0 8px 0'>Not part of the core journey. Skipping changes nothing in your fit results.</div>")
            es = S.eq_stage
            if es == "offer":
                c = st.columns([1, 2, 4])
                with c[0]: st.button("SKIP", key="eq_skip", on_click=lambda: S.update(eq_stage="skipped"))
                with c[1]: st.button("TAKE EQ SELF-ASSESSMENT", key="eq_take", type="primary", on_click=lambda: S.update(eq_stage="taking"))
            elif es == "skipped":
                ui.md("<div class='nd-note'>EQ skipped — everything else works the same.</div>"); st.button("Take it anyway", key="eq_change", on_click=lambda: S.update(eq_stage="taking"))
            else:
                import eq   # lazy: only loaded when the user asks
                ui.md(f"<div class='nd-warn'>{ui.esc(eq.DISCLAIMER)}</div>")
                if es == "taking":
                    for i, (dim, text, rev) in enumerate(eq.ITEMS):
                        cc = st.columns([3, 2], vertical_alignment="center"); cc[0].markdown(f"<div style='font-size:13px'><span class='nd-label' style='margin-right:8px'>{dim.upper()}</span>{ui.esc(text)}</div>", unsafe_allow_html=True)
                        with cc[1]: st.segmented_control(text, [1, 2, 3, 4, 5], key=f"eq_{i}", label_visibility="collapsed")
                    cb = st.columns([1.3, 1, 4])
                    with cb[0]: st.button("SEE INDICATIVE REPORT", key="eq_done", type="primary", on_click=lambda: S.update(eq_stage="done"))
                    with cb[1]: st.button("CANCEL", key="eq_cancel", on_click=lambda: S.update(eq_stage="offer"))
                else:
                    sc = eq.score({i: S.get(f"eq_{i}") for i in range(len(eq.ITEMS))})
                    if not sc: ui.warn("No EQ answers yet.")
                    else:
                        ui.md("<table class='nd-tbl'><tr><th>Dimension</th><th>Self-rated (1–5)</th><th>Indicative band</th></tr>" + "".join(f"<tr><td>{ui.esc(d)}</td><td>{v['value']:.1f} ({v['n']} items)</td><td>{ui.chip(v['band'], {'Strong':'teal','Solid':'blue','Developing':'amber'}[v['band']])}</td></tr>" for d, v in sc.items()) + "</table>")
                    if S.get("user") and sc:
                        c5 = st.columns([2, 2, 3])
                        with c5[0]: st.button("SAVE ENCRYPTED TO MY ACCOUNT", key="eq_save", on_click=lambda: (auth.save_private(S.user, "eq", dict(answers={i: S.get(f"eq_{i}") for i in range(len(eq.ITEMS))}, bands={d: v["band"] for d, v in sc.items()})), S.update(eq_saved=True)))
                        with c5[1]: st.button("DELETE SAVED COPY", key="eq_del_saved", on_click=lambda: (auth.delete_private(S.user, "eq"), S.update(eq_saved=False)))
                        ui.md("<div class='nd-sub'>Saved reports are encrypted with a key derived from your password — the operator and any organisation cannot read them. Opt-in only.</div>" + ("<div class='nd-note'>Saved ✓</div>" if S.get("eq_saved") else ""))
                    elif not S.get("user"): ui.md("<div class='nd-sub'>Guest session: nothing is stored. Sign in to save an encrypted copy (optional).</div>")
                    ui.prov("eq", "eq"); st.button("DELETE MY EQ ANSWERS", key="eq_del", on_click=lambda: ([S.pop(f"eq_{i}", None) for i in range(15)], S.update(eq_stage="offer")))
        c = st.columns([1, 1, 4])
        with c[0]: st.button("RETAKE ASSESSMENT", key="dna_retake", on_click=lambda: S.update(dna_stage="intro", dna_q=0, dna_ans={}))
        ui.footer()


# ============================================================================ EVIDENCE
def evidence_rows(R):
    out = []
    cl = R.get("cleaning", {}); ja = R.get("jds_audit", {})
    out.append(("Analytics Jobs", f"{cl.get('raw',0):,} → {cl.get('clean',0):,}", "Exact-duplicate removal, parsing, taxonomy", f"{cl.get('dup',0):,} duplicates · {cl.get('trunc_pct',0):.1f}% skills truncated", "—", "Analytics_Jobs.csv", "01", "No exact salaries; truncated skills", "OBSERVED", "cleaning"))
    ov = R.get("id_overlap", {}); out.append(("All four", "—", "Identifier overlap audit", f"JDS ∩ SDS = {ov.get('JDS.id ∩ SDS.id', 0)} ids", "—", "all four files", "01", "No valid row-level join → taxonomy bridge", "OBSERVED", "id_overlap"))
    for e in R.get("jds_effects", []):
        out.append(("JDS", f"n = {ja.get('n', 139)}", "Mann–Whitney U + Cliff's δ", f"{LABEL[e['skill']]}: δ = {e['delta']:.2f}", f"[{e['ci_lo']:.2f}, {e['ci_hi']:.2f}]", "JDS_Skill_Traits.xlsx", "02", "One company; association only", "DERIVED", "jds_effects"))
    t1 = R.get("t1_models", {}); b1 = t1.get("NEXUS L2 logistic (C=1)")
    if b1: out.append(("JDS", f"n = {ja.get('n', 139)}", "L2 logistic, grouped CV ×20 (7-model zoo)", f"AUC {b1['auc']:.3f} · Brier {b1['brier']:.3f}", f"± {b1['auc_sd']:.3f} (SD over repeats)", "JDS_Skill_Traits.xlsx", "03", "Single company; permutation p < " + f"{R.get('t1_validation', {}).get('p', 0):.4f}", "DERIVED", "t1_models"))
    mo = R.get("market_or", {}); s5 = "S5 +all controls (primary tax.)"
    for k in ["ai_ml", "coding", "maths_stats", "big_data", "story"]:
        v = mo.get(s5, {}).get(k)
        if v: out.append(("Analytics Jobs", f"n = {cl.get('ds_primary', 0):,}", "Ordinal logit, 6 bands", f"{LABEL[k]}: OR = {v['OR']:.2f}", f"[{v['lo']:.2f}, {v['hi']:.2f}]", "Analytics_Jobs.csv", "04", "Banded salary; association", "DERIVED", "market_or"))
    sd = R.get("story_decomp")
    if sd:
        for nm, kk in (("Visualisation tools", "viz"), ("MIS / reporting-only", "mis_only")): out.append(("Analytics Jobs", f"n = {sd.get('n', 0):,}", "Ordinal logit, decomposition", f"{nm}: OR = {sd[kk]['OR']:.2f}", f"[{sd[kk]['lo']:.2f}, {sd[kk]['hi']:.2f}]", "Analytics_Jobs.csv", "04", "MIS-only is also a role proxy", "DERIVED", "story_decomp"))
    t2 = R.get("t2_models", {}); v2 = R.get("t2_validation", {}); bst = v2.get("best")
    if bst and bst in t2: out.append(("Analytics Jobs", f"n = {v2.get('n', 0):,}", "TF-IDF + structured LR, GroupKFold (7-model zoo)", f"exact-band {t2[bst]['acc']:.0%} · κ {t2[bst]['qwk']:.2f} · ±1 band {t2[bst]['within1']:.0%}", f"flag gain κ +{v2.get('qwk_gain', 0):.3f} [{v2.get('qwk_gain_lo', 0):.3f}, {v2.get('qwk_gain_hi', 0):.3f}]", "Analytics_Jobs.csv", "05", "Accuracy < 50% → distribution only", "DERIVED", "t2_models"))
    hr = R.get("headroom", {})
    for i, k in enumerate(hr.get("skills", [])): out.append(("JDS", f"n = {ja.get('n', 139)}", "What-if E_k, 1,000 bootstrap refits", f"{LABEL[k]}: {hr['Ek'][i]:.2f} pp · headroom {hr['headroom'][i]*100:.0f}%", f"[{hr['ci_lo'][i]:.2f}, {hr['ci_hi'][i]:.2f}]", "JDS_Skill_Traits.xlsx", "06", "What-if association, not causal", "INFERRED", "headroom"))
    for k, v in R.get("ladder", {}).items(): out.append(("DataScience Jobs", f"{v['n']} companies", "Paired senior/junior ratio + Wilcoxon", f"{k}: {v['median_ratio']:.2f}×", f"[{v['lo']:.2f}, {v['hi']:.2f}]", "DataScience_Jobs.csv", "06", "No dates: structural, not trend", "OBSERVED", "ladder"))
    sds = R.get("sds")
    if sds: out.append(("SDS", f"n = {sds['n']}", "Cliff's δ per trait + grouped-CV logistic", f"AUC {sds['auc_mean']:.2f} (exploratory)", f"± {sds['auc_sd']:.3f}", "SDS_Personality_Traits.xlsx", "02", "Cohort context only — NOT an EQ score", "OBSERVED", "sds"))
    return out


def page_evidence(b):
    with st.container(key="body"):
        ui.header("This is not just a UI.", "Every figure in NEXUS DELTA traces to a dataset, a method, an interval, a notebook and a limitation.", "EVIDENCE · FOR JUDGES")
        if not b.ok_results: ui.err("results.json unavailable — run notebooks 01–07."); ui.footer(); return
        R = b.results
        ui.md("<div style='display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:10px'>" + " ".join([
            ui.chip("PYTHON · EXECUTED (7 Colab notebooks)", "teal"), ui.chip("SQL · EXECUTED (SQLite; MySQL-compatible DDL)", "teal"), ui.chip("SAS · TEMPLATE, NOT EXECUTED", "amber"), ui.chip("STREAMLIT · THIS APP, OFFLINE", "blue")]) + "</div>")
        ui.md("<div style='display:flex;flex-wrap:wrap;gap:6px;align-items:center'>" + " <span style='color:#8D99AE'>→</span> ".join(ui.chip(s, "ink" if i == 3 else "grey") for i, s in enumerate(["DATA", "EVIDENCE", "INSIGHT", "DECISION", "ACTION"])) + "<span class='nd-sub' style='margin-left:10px'>Four datasets stay separate at row level; they connect through the versioned capability taxonomy — never a fake join.</span></div>")
        rows = evidence_rows(R)
        flt = st.segmented_control("Dataset", ["ALL", "JDS", "Analytics Jobs", "DataScience Jobs", "SDS"], key="ev_filter", default="ALL", required=True, label_visibility="collapsed")
        sel = [r for r in rows if flt == "ALL" or r[0] == flt]
        ui.md("<table class='nd-tbl'><tr><th>Dataset</th><th>Sample</th><th>Method</th><th>Metric</th><th>95% CI / spread</th><th>Source</th><th>Notebook</th><th>Limitation</th><th>Label</th></tr>" + "".join(
            f"<tr><td>{ui.esc(r[0])}</td><td>{ui.esc(r[1])}</td><td>{ui.esc(r[2])}</td><td><b>{ui.esc(r[3])}</b></td><td>{ui.esc(r[4])}</td><td>{ui.esc(r[5])}</td><td>NB{r[6]}</td><td>{ui.esc(r[7])}</td><td>{ui.evidence_chip(r[8])}</td></tr>" for r in sel) + "</table>")
        ui.md("<div class='nd-label' style='margin:18px 0 6px 0'>PROVENANCE EXPLORER</div>")
        pk = st.selectbox("Open provenance for", list(PROV), format_func=lambda k: f"{k} — {PROV[k]['method'][:70]}", key="ev_prov", label_visibility="collapsed")
        p = PROV[pk]
        with st.container(key="card_prov"):
            c = st.columns(5)
            for col, (lab, val) in zip(c, [("SOURCE FILE", p["file"]), ("NOTEBOOK", config.NB.get(p["nb"], p["nb"])), ("RESULT JSON KEY", p["key"]), ("METHOD", p["method"]), ("LIMITATION", p["limit"])]): col.markdown(f"<div class='nd-label'>{lab}</div><div style='font-size:12.5px;line-height:1.4'>{ui.esc(val)}</div>", unsafe_allow_html=True)
            ui.md(f"<div style='margin-top:8px'>{ui.evidence_chip(p['label'])} <span class='nd-sub'>{ui.esc(config.EVIDENCE_LABELS[p['label']][0])}</span></div>")
        sec = st.segmented_control("Charts", ["INTERNAL (JDS)", "MARKET", "MODELS", "DATA QUALITY", "CAREER LADDER"], key="ev_chart", default="INTERNAL (JDS)", required=True, label_visibility="collapsed")
        with st.container(key="card_evchart"):
            if sec == "INTERNAL (JDS)":
                c = st.columns(2)
                with c[0]: ui.md("<div class='nd-label'>CLIFF'S δ — HIGH vs LOW HIKE JUNIORS</div>"); st.plotly_chart(charts.effects_forest(R["jds_effects"]), width="stretch", config={"displayModeBar": False}, key="ev_forest")
                with c[1]:
                    ce = R.get("jds_ceiling", {}); ui.md("<div class='nd-label'>SHARE AT THE 5.0 CEILING</div>" + "".join(f"<div style='display:flex;justify-content:space-between;font-size:13px;border-bottom:1px solid {C['line']};padding:5px 0'><span>{LABEL[k]}</span><b>{v:.0%}</b></div>" for k, v in sorted(ce.items(), key=lambda kv: -kv[1])))
            elif sec == "MARKET":
                st.plotly_chart(charts.market_forest(R["market_or"]), width="stretch", config={"displayModeBar": False}, key="ev_market")
                pr, ds_ = R.get("market_premium_specs", {}), R.get("market_discount_specs", {})
                ui.md("<div class='nd-sub'>Specifications with a significant premium (of 6): " + " · ".join(f"{SHORT[k]} {pr.get(k,0)}/6" for k in CAPS) + " · discount: " + " · ".join(f"{SHORT[k]} {ds_.get(k,0)}/6" for k in CAPS if ds_.get(k, 0)) + "</div>")
            elif sec == "MODELS":
                c = st.columns(2)
                with c[0]: ui.md("<div class='nd-label'>T1 HIGH-HIKE · AUC (7 models, grouped CV)</div>"); st.plotly_chart(charts.model_compare(R["t1_models"], "auc", 300, "NEXUS L2 logistic (C=1)"), width="stretch", config={"displayModeBar": False}, key="ev_t1")
                with c[1]: ui.md("<div class='nd-label'>T2 SALARY BAND · WEIGHTED κ (7 models)</div>"); st.plotly_chart(charts.model_compare(R["t2_models"], "qwk", 300, R.get("t2_validation", {}).get("best"), "weighted κ"), width="stretch", config={"displayModeBar": False}, key="ev_t2")
            elif sec == "DATA QUALITY":
                cl = R["cleaning"]; ui.md("<table class='nd-tbl'><tr><th>Cleaning step</th><th>Rows</th></tr>" + "".join(f"<tr><td>{ui.esc(k)}</td><td>{v:,}</td></tr>" for k, v in cl["log"]) + f"<tr><td>truncated key_skills</td><td>{cl['trunc']:,} ({cl['trunc_pct']:.1f}%)</td></tr><tr><td>job_type missing (raw)</td><td>12,011 (75.8%)</td></tr></table>")
            else:
                st.plotly_chart(charts.ladder_chart(R["ladder"]), width="stretch", config={"displayModeBar": False}, key="ev_ladder")
        ui.md("<div class='nd-label' style='margin:14px 0 6px 0'>REPRODUCE</div><div class='nd-note'>Open the notebooks in <code>notebooks/</code> in Google Colab and run 01 → 07 (seed 42, ≈ 5 min). They write <code>out/results.json</code> — the single source for this app and the Approach Note. The SAS script <code>nexus_delta_sas_mirror.sas</code> mirrors the Wilcoxon, logistic and cumulative-logit steps but has not been executed.</div>")
        ui.footer()


# ============================================================================ ABOUT
def page_about(b):
    with st.container(key="body"):
        ui.header("NEXUS DELTA", "An evidence-first capability intelligence and development decision engine — not an HR dashboard, ATS, chatbot or recommender.", "ABOUT")
        c = st.columns([1.2, 1], gap="large")
        with c[0], st.container(key="card_about"):
            ui.md(f"<div class='nd-label'>THE QUESTION</div><div style='font-size:14px;line-height:1.6'><b>Organisations:</b> what capability should we develop next?<br><b>Students / professionals:</b> what should I develop next for the role I want?<br><b>Role fit:</b> will the way this role works fit the way I work?</div>"
                  f"<div class='nd-label' style='margin-top:14px'>HOW IT WORKS</div><div style='font-size:13.5px;line-height:1.6'>Four organiser datasets stay separate at row level (different grains, no valid shared key). They connect through a versioned capability taxonomy: internal outcome association (JDS) + market salary-band association (Analytics Jobs) + career ladder (Data Science Jobs) + cohort context (SDS). Printed rules turn the evidence into a verdict, with uncertainty.</div>"
                  f"<div class='nd-label' style='margin-top:14px'>TEAM</div><div style='font-size:13.5px'><b>Team DSA</b> — {' · '.join(config.BRAND['members'])}<br>Chandigarh University · Build For Bharat 2.0</div>")
        with c[1], st.container(key="card_labels"):
            ui.md("<div class='nd-label'>EVIDENCE LABELS</div>" + "".join(f"<div style='margin:6px 0;font-size:12.5px'>{ui.evidence_chip(k)} &nbsp;{ui.esc(v[0])}</div>" for k, v in config.EVIDENCE_LABELS.items()))
        ui.md("<div class='nd-label' style='margin:18px 0 6px 0'>HOW NEXUS DELTA PROTECTS YOU</div>")
        prot = [("No covert interview assistance", "NEXUS DELTA never listens during an interview or feeds answers."), ("No hidden answer generation", "It shows evidence and questions to ask — never scripted answers."), ("No emotion recognition", "Voice and text are never analysed for emotion."),
                ("No voice-based personality inference", "Speech is transcribed locally and discarded; nothing is inferred about the speaker."), ("No automatic hiring or rejection", "Organisation view labels are discussion prompts; a human decides."),
                ("No clinical EQ claim", "The optional EQ report is an indicative self-assessment only; the SDS dataset is not an EQ score."), ("No burnout diagnosis", "Work DNA reports work-style friction, never a diagnosis or prediction."),
                ("Consent for self-assessment", "Work DNA and EQ require consent and stay in your browser session."), ("User control over optional EQ", "Skip, take, or delete it at any time; it never feeds the fit results."),
                ("Explainability", "Every number has a provenance badge: source file, notebook, JSON key, method, limitation."), ("Uncertainty", "Intervals, bootstrap win-rates and probability bands are always shown."), ("Human override", "Ties are declared, not hidden; overrides are the human's call."),
                ("Encrypted at rest", "AES-256-GCM per record; passwords scrypt-hashed; master key kept outside the database."), ("Anonymous culture ratings", "Employee answers carry no user id; nothing is shown below 5 responses."), ("Private by key", "A saved EQ report is encrypted with a key derived from your password.")]
        cc = st.columns(3)
        for i, (t, d) in enumerate(prot):
            with cc[i % 3], st.container(key=f"card_prot_{i}"): ui.md(f"<div style='font-weight:700;font-size:13px'>{ui.esc(t)}</div><div class='nd-sub'>{ui.esc(d)}</div>")
        ui.md("<div class='nd-label' style='margin:18px 0 6px 0'>WHAT IS OBSERVED vs PROPOSED</div>")
        ui.md("<table class='nd-tbl'><tr><th>Feature</th><th>Status</th><th>Note</th></tr>"
              f"<tr><td>Capability Evidence Matrix, verdicts, headroom</td><td>{ui.evidence_chip('DERIVED')}</td><td>From the executed notebooks; E_k is {ui.evidence_chip('INFERRED')} (what-if).</td></tr>"
              f"<tr><td>Role profiles and capability demand (Career Intelligence)</td><td>{ui.evidence_chip('DERIVED')}</td><td>Measured on matching postings; student priorities are rule-based and PROPOSED.</td></tr>"
              f"<tr><td>JD Scanner: tags and salary-band distribution</td><td>{ui.evidence_chip('DERIVED')}</td><td>Taxonomy regex + selected T2 model (≈ 44% exact-band).</td></tr>"
              f"<tr><td>Work-style cues from a JD</td><td>{ui.evidence_chip('PROPOSED')}</td><td>Keyword lexicon; not validated.</td></tr>"
              f"<tr><td>Work DNA self-assessment and friction rules</td><td>{ui.evidence_chip('PROPOSED')}</td><td>Not validated against the supplied data.</td></tr>"
              f"<tr><td>Employee-reported culture ratings</td><td>{ui.evidence_chip('PROPOSED')}</td><td>Self-report by invite-verified employees; instrument not validated; demo organisation is SIMULATED.</td></tr>"
              f"<tr><td>Illustrative role profiles</td><td>{ui.evidence_chip('SIMULATED')}</td><td>Hand-written; not company measurements.</td></tr>"
              f"<tr><td>Optional EQ report</td><td>{ui.evidence_chip('PROPOSED')}</td><td>Indicative self-assessment only.</td></tr>"
              f"<tr><td>Hear (voice)</td><td>{ui.evidence_chip('PROPOSED')}</td><td>Needs a local offline speech model (Vosk / faster-whisper); the text fallback always works.</td></tr></table>")
        ui.md("<div class='nd-label' style='margin:18px 0 6px 0'>KNOWN LIMITATIONS</div><div class='nd-note'>Single-company outcome data (n = 139) · skill text truncated in 87% of postings · banded salary only · regex taxonomy not hand-audited · Tier-2/3 samples are small · no company work-style measurements exist, so Role Work DNA is illustrative.</div>")
        ui.footer()


# ============================================================================ main
@st.cache_resource(show_spinner=False)
def _demo_seed():
    """fresh server (e.g. Streamlit Cloud restart): create the SIMULATED demo org + accounts once. Disable with NEXUS_DEMO_SEED=0."""
    import os
    if os.environ.get("NEXUS_DEMO_SEED", "1") == "0": return "off"
    try:
        import seed_demo; return seed_demo.run()
    except Exception as e: return f"seed failed: {e}"


def main():
    init_state(); b = data.get_bundle(); _demo_seed()
    ui.md(ui.css(S.page, S.cap_sel if S.page == "CAPABILITY INTELLIGENCE" else None))
    if not AC.logged_in():
        ui.shell("", go, show_nav=False); AC.login_page(); return
    ui.shell(S.page, go, account=AC.account_chip(), on_logout=AC.logout)
    if S.demo_on: demo_bar()
    for k, e in b.errors.items():
        if k in ("taxonomy", "model", "artifacts"): ui.md(f"<div style='max-width:1320px;margin:6px auto;padding:0 32px'><div class='nd-warn'>Optional data missing — {ui.esc(e)}. The app continues with reduced features.</div></div>")
    {"HOME": page_home, "CAPABILITY INTELLIGENCE": page_capability, "CAREER INTELLIGENCE": page_career, "JD SCANNER": page_scanner, "WORK DNA": page_workdna, "CULTURE": lambda b: AC.page_culture(b, go), "EVIDENCE": page_evidence, "ABOUT": page_about}[S.page](b)


main()
