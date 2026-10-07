"""Executive layer: 3D hero, overview metrics, priority ranking, Evidence Convergence, Insights, NEXUS DECISION.
All values come from results.json (via decision_engine.build_matrix). Decisions are the notebooks' printed verdicts, re-labelled:
FUND -> PRIORITIZE · FUND WITH REFRAME / TIED / MONITOR -> INVESTIGATE · DEPRIORITISE -> MAINTAIN. Nothing is re-scored here."""
import streamlit as st
import plotly.graph_objects as go_
import ui, decision_engine as de
from config import C, LABEL, SHORT

DECISION = {"FUND": "PRIORITIZE", "FUND WITH REFRAME": "INVESTIGATE", "TIED": "INVESTIGATE", "MONITOR": "INVESTIGATE", "DEPRIORITISE": "MAINTAIN"}
DCOL = {"PRIORITIZE": C["blue"], "INVESTIGATE": C["gold"], "MAINTAIN": C["grey"]}
ORDER = {"PRIORITIZE": 0, "INVESTIGATE": 1, "MAINTAIN": 2}


def _lvl_internal(m): return {"Strong": "HIGH", "Moderate": "MEDIUM"}.get(m, "LOW")   # notebook rule: Strong = δ ≥ 0.33 and CI > 0
def _lvl_market(m): return {"Premium": "HIGH", "Neutral": "MEDIUM"}.get(m, "LOW")                    # premium in 6/6 specs / neutral / discount in 6/6
def _lvl_head(h): return "HIGH" if h >= 60 else ("MEDIUM" if h >= 45 else "LOW")                    # % of juniors below the 5.0 ceiling


def rows(results):
    out = []
    for m in de.build_matrix(results):
        d = DECISION.get(m["verdict_display"], "INVESTIGATE")
        r = dict(key=m["key"], name=LABEL[m["key"]], decision=d, verdict=m["verdict_display"], delta=m["delta"], OR=m["OR_primary"], market=m["market"],
                 headroom=m["headroom"], Ek=m["Ek"], Ek_lo=m["Ek_lo"], Ek_hi=m["Ek_hi"],
                 li=_lvl_internal(m.get("internal")), lm=_lvl_market(m["market"]), lh=_lvl_head(m["headroom"]))
        r["conflict"] = (r["li"] != "LOW" and r["lm"] == "LOW") or (r["li"] == "LOW" and r["lm"] == "HIGH")   # directions disagree
        r["why"] = why(r); out.append(r)
    out.sort(key=lambda r: (ORDER[r["decision"]], -r["Ek"]))
    return out


def why(r):
    i = {"HIGH": "Strong internal association", "MEDIUM": "Moderate internal association", "LOW": "No significant internal association"}[r["li"]] + f" (δ {r['delta']:.2f})"
    m = {"HIGH": f"a market premium (odds ratio {r['OR']:.2f}, significant in 6/6 models)", "MEDIUM": f"no reliable market premium (OR {r['OR']:.2f})",
         "LOW": f"a market discount (OR {r['OR']:.2f}, in 6/6 models)"}[r["lm"]]
    h = f"{r['headroom']:.0f}% of juniors still below the ceiling"
    if r["decision"] == "PRIORITIZE": return f"{i} + {m} + {h}. Signals converge."
    if r["decision"] == "MAINTAIN": return f"{i}. High headroom alone is not a reason to invest: {h}, but the univariate internal link is not significant; revisit with more data."
    return f"{i}, but {m}. Signals conflict: the discount sits with MIS/reporting keywords (visualisation alone is neutral), so reframe toward analytical communication."


def hero_3d(height=430):
    """lightweight canvas: ~90 nodes on a sphere, nearest-neighbour edges, 1 rotation / ~60 s; pauses off-screen; static if reduced motion."""
    st.iframe(f"""<!doctype html><html><body style="margin:0;background:transparent;overflow:hidden"><canvas id=c style="width:100%;height:{height}px;display:block"></canvas><script>
const cv=document.getElementById('c'),x=cv.getContext('2d');let W,H,D=devicePixelRatio||1;
function rs(){{W=cv.clientWidth;H=cv.clientHeight;cv.width=W*D;cv.height=H*D;x.setTransform(D,0,0,D,0,0)}}rs();addEventListener('resize',rs);
const N=90,P=[],g=Math.PI*(3-Math.sqrt(5));for(let i=0;i<N;i++){{const y=1-2*i/(N-1),r=Math.sqrt(1-y*y),t=g*i;P.push([Math.cos(t)*r,y,Math.sin(t)*r])}}
const E=[];for(let i=0;i<N;i++){{const d=P.map((p,j)=>[j,(p[0]-P[i][0])**2+(p[1]-P[i][1])**2+(p[2]-P[i][2])**2]).sort((a,b)=>a[1]-b[1]);for(let k=1;k<4;k++)if(i<d[k][0])E.push([i,d[k][0]])}}
const HUB={{7:'Talent',29:'Skills',53:'Market',77:'Decision'}};const COL=['#E07A1F','#2F8F62','#B8963E','#F5F1E8'];
const red=matchMedia('(prefers-reduced-motion: reduce)').matches;let a=0.6,vis=true;new IntersectionObserver(e=>vis=e[0].isIntersecting).observe(cv);
function f(){{if(vis||a===0.6){{x.clearRect(0,0,W,H);const R=Math.min(W,H)*0.38,cx=W/2,cy=H/2,ca=Math.cos(a),sa=Math.sin(a),tl=0.35,ct=Math.cos(tl),st=Math.sin(tl);
const Q=P.map(p=>{{let X=p[0]*ca+p[2]*sa,Z=-p[0]*sa+p[2]*ca,Y=p[1]*ct-Z*st;Z=p[1]*st+Z*ct;const s=1/(1.9-Z*0.6);return[cx+X*R*s*1.25,cy+Y*R*s*1.25,Z]}});
x.lineWidth=0.7;for(const[i,j]of E){{const z=(Q[i][2]+Q[j][2])/2;x.strokeStyle=`rgba(184,198,228,${{0.10+0.25*(z+1)/2}})`;x.beginPath();x.moveTo(Q[i][0],Q[i][1]);x.lineTo(Q[j][0],Q[j][1]);x.stroke()}}
Q.forEach((q,i)=>{{const z=(q[2]+1)/2,h=HUB[i];x.globalAlpha=0.35+0.65*z;x.fillStyle=h?COL[Object.keys(HUB).indexOf(String(i))]:'#8FA3C9';x.beginPath();x.arc(q[0],q[1],h?4+3*z:1.2+1.6*z,0,7);x.fill();
if(h&&z>0.45){{x.font='600 11px Inter,Segoe UI,sans-serif';x.fillStyle='#F5F1E8';x.globalAlpha=z;x.fillText(h.toUpperCase(),q[0]+9,q[1]+4)}}}});x.globalAlpha=1;
if(!red)a+=0.0017}}requestAnimationFrame(f)}}f();</script></body></html>""", height=height)


def overview(b, go, open_cap):
    with st.container(key="exhero"):
        L, R = st.columns([1.15, 1], vertical_alignment="center")
        with L:
            ui.md("<div class='nd-kicker' style='color:#F4A259'>BUILD FOR BHARAT 2.0 · TEAM DSA</div>"
                  "<div class='ex-title'>NEXUS DELTA</div><div class='ex-h2'>Evidence-based capability intelligence for the future workforce.</div>"
                  "<div class='ex-p'>From workforce data to evidence-backed capability decisions — internal evidence, market evidence and capability headroom, weighed separately and never averaged.</div>")
            c = st.columns([1.2, 1, 1.6])
            with c[0]: st.button("Explore NEXUS DELTA →", key="cta_explore", type="primary", on_click=go, args=("CAPABILITY INTELLIGENCE",))
            with c[1]: st.button("View Evidence →", key="cta_evidence", on_click=go, args=("EVIDENCE",))
        with R: hero_3d()
    if not b.ok_results: return
    with st.container(key="exbody"): _overview_body(b, open_cap)


def _overview_body(b, open_cap):
    R_ = rows(b.results); cl = b.results.get("cleaning", {}); dec = b.results.get("decision", {})
    n_pri = sum(r["decision"] == "PRIORITIZE" for r in R_); n_conf = sum(r["conflict"] for r in R_)
    cards = [("◇", "CAPABILITIES ANALYSED", len(R_), "", "versioned taxonomy cap-tax-v2.0"),
             ("◎", "MARKET SIGNALS", cl.get("clean", 0), "", f"job postings after removing {cl.get('dup', 0):,} duplicates"),
             ("◆", "EVIDENCE CONFIDENCE", round(100 * dec.get("p_beat", 0)), "%", f"top lever wins {dec.get('p_beat', 0)*100:.1f}% of 1,000 bootstrap refits (rule: ≥ 80%)"),
             ("▲", "PRIORITY CAPABILITIES", n_pri, "", "converging internal + market evidence"),
             ("⚑", "CONFLICTING SIGNALS", n_conf, "", "internal and market evidence disagree")]
    ui.md("<div class='ex-cards'>" + "".join(f"<div class='ex-card' style='animation-delay:{i*70}ms'><div class='ex-ic'>{ic}</div><div class='nd-label'>{lab}</div>"
          f"<div class='ex-num'>{(f'{v:,}' if v >= 1000 else f'<span class=ex-count style=--to:{v}></span>')}{suf}</div><div class='nd-sub'>{sub}</div></div>" for i, (ic, lab, v, suf, sub) in enumerate(cards)) + "</div>")
    ui.md("<div class='ex-sec'>CAPABILITY PRIORITY</div><div class='nd-sub' style='margin-bottom:10px'>Ranked by decision, then by modelled gain (E<sub>k</sub>, pp per +0.5 step). The bar is the gain; the label is the decision.</div>")
    mx = max(r["Ek"] for r in R_) or 1
    for i, r in enumerate(R_, 1):
        with st.container(key=f"exrank_{r['key']}"):
            c = st.columns([0.35, 2.6, 4.4, 1.1], vertical_alignment="center")
            c[0].markdown(f"<div class='ex-rk'>{i:02d}</div>", unsafe_allow_html=True)
            c[1].markdown(f"<div class='ex-nm'>{r['name']}</div>{dchip(r['decision'])}", unsafe_allow_html=True)
            c[2].markdown(f"<div class='ex-bar'><span style='width:{100*r['Ek']/mx:.0f}%;background:{DCOL[r['decision']]};animation-delay:{i*90}ms'></span></div>"
                          f"<div class='nd-sub'><b>Why?</b> {ui.esc(r['why'])}</div>", unsafe_allow_html=True)
            with c[3]: st.button("Evidence ›", key=f"exwhy_{r['key']}", on_click=open_cap, args=(r["key"],))


def dchip(d): return f"<span class='ex-d' style='color:{DCOL[d]};border-color:{DCOL[d]}'>{d}</span>"
def lchip(l): return f"<span class='ex-l ex-{l.lower()}'>{l}</span>"


def convergence(b):
    if not b.ok_results: return
    ui.md("<div class='ex-sec'>EVIDENCE CONVERGENCE</div><div class='nd-sub' style='margin-bottom:10px'>Three independent signals per capability. NEXUS DELTA does not average them — "
          "agreement leads to PRIORITIZE, disagreement to INVESTIGATE, a weak internal link to MAINTAIN.</div>")
    R_ = rows(b.results); cols = st.columns(len(R_), gap="small")
    for col, r in zip(cols, R_):
        with col:
            ui.md(f"<div class='ex-conv{' ex-conflict' if r['conflict'] else ''}'><div class='ex-nm' style='font-size:15px'>{r['name']}</div>"
                  f"<div class='ex-row'><span>Internal</span>{lchip(r['li'])}</div><div class='ex-row'><span>Market</span>{lchip(r['lm'])}</div><div class='ex-row'><span>Headroom</span>{lchip(r['lh'])}</div>"
                  f"<div class='ex-arrow'>↓</div><div style='text-align:center'>{dchip(r['decision'])}</div>"
                  f"<div class='nd-sub' style='margin-top:8px'>{'⚑ conflict · ' if r['conflict'] else ''}{ui.esc(r['why'])}</div></div>")
    ui.md("<div class='nd-sub' style='margin-top:6px'>Levels: internal = the decision rule (HIGH: δ ≥ 0.33 with 95% CI above 0; LOW: not significant after Holm or δ < 0.147) · market = premium / neutral / discount across 6 ordinal-logit specifications · "
          "headroom = share of juniors below the 5.0 ceiling, ≥ 60% HIGH, 45–60% MEDIUM, < 45% LOW. Decisions are the notebook verdicts (FUND → PRIORITIZE, FUND WITH REFRAME → INVESTIGATE, DEPRIORITISE → MAINTAIN).</div>")


def _fig(h=300):
    f = go_.Figure(); f.update_layout(height=h, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                      font=dict(family="Inter, Segoe UI, sans-serif", size=12, color=C["ink"]), showlegend=False,
                                      transition=dict(duration=500, easing="cubic-in-out")); return f


def insights(b):
    R_ = rows(b.results); res = b.results
    ui.md("<div class='ex-sec'>EVIDENCE CONFLICT MATRIX</div>")
    f = _fig(380)
    f.add_shape(type="rect", x0=1, x1=2.1, y0=0.33, y1=0.8, fillcolor="rgba(47,143,98,.08)", line_width=0); f.add_shape(type="line", x0=1, x1=1, y0=0, y1=0.8, line=dict(color=C["line"], dash="dot"))
    f.add_shape(type="rect", x0=0.55, x1=1, y0=0.33, y1=0.8, fillcolor="rgba(184,150,62,.10)", line_width=0); f.add_shape(type="line", x0=0.55, x1=2.1, y0=0.33, y1=0.33, line=dict(color=C["line"], dash="dot"))
    for txt, x, y in [("CONVERGENCE", 1.75, 0.78), ("INTERNAL-LED (conflict)", 0.7, 0.78), ("MARKET-LED", 1.75, 0.02), ("WEAK BOTH", 0.7, 0.02)]:
        f.add_annotation(x=x, y=y, text=txt, showarrow=False, font=dict(size=10, color=C["muted"]))
    for r in R_:
        f.add_trace(go_.Scatter(x=[r["OR"]], y=[r["delta"]], mode="markers+text", text=[SHORT[r["key"]]], textposition="top center",
                                marker=dict(size=12 + r["headroom"] / 5, color=DCOL[r["decision"]], line=dict(color="#fff", width=1.5)),
                                hovertemplate=f"{r['name']}<br>internal δ {r['delta']:.2f}<br>market OR {r['OR']:.2f}<br>headroom {r['headroom']:.0f}%<br>{r['decision']}<extra></extra>"))
    f.update_xaxes(title="Market evidence — odds ratio for a higher salary band (all controls)", range=[0.55, 2.1], gridcolor=C["line"]); f.update_yaxes(title="Internal evidence — Cliff's δ", range=[0, 0.8], gridcolor=C["line"])
    st.plotly_chart(f, width="stretch", config={"displayModeBar": False}, key="ex_cm")
    ui.md("<div class='nd-sub'>Bubble size = headroom. Dotted lines: OR = 1 (no market effect) and δ = 0.33 (medium internal effect).</div>")
    L, Rr = st.columns(2, gap="large")
    with L:
        ui.md("<div class='ex-sec'>CAPABILITY vs INTERNAL OUTCOMES</div>")
        eff = sorted(res.get("jds_effects", []), key=lambda e: e["delta"]); f = _fig(280)
        f.add_trace(go_.Scatter(x=[e["delta"] for e in eff], y=[LABEL.get(e["skill"], e["skill"]) for e in eff], mode="markers", marker=dict(size=11, color=C["navy"]),
                                error_x=dict(type="data", symmetric=False, array=[e["ci_hi"] - e["delta"] for e in eff], arrayminus=[e["delta"] - e["ci_lo"] for e in eff], color=C["grey"])))
        f.add_vline(x=0, line=dict(color=C["line"])); f.update_xaxes(title="Cliff's δ (95% bootstrap CI) · high vs low hike, JDS n = 139"); st.plotly_chart(f, width="stretch", config={"displayModeBar": False}, key="ex_int")
    with Rr:
        ui.md("<div class='ex-sec'>CAPABILITY vs MARKET DEMAND</div>")
        mk = sorted(R_, key=lambda r: r["OR"]); f = _fig(280)
        f.add_trace(go_.Bar(x=[r["OR"] - 1 for r in mk], y=[r["name"] for r in mk], base=1, orientation="h", marker_color=[C["teal"] if r["OR"] > 1 else C["red"] for r in mk],
                            text=[f"{r['OR']:.2f}" for r in mk], textposition="outside"))
        f.add_vline(x=1, line=dict(color=C["ink"], width=1)); f.update_xaxes(title="Odds ratio for a higher salary band (1 = no effect)", range=[0.6, 1.75]); st.plotly_chart(f, width="stretch", config={"displayModeBar": False}, key="ex_mkt")
    L, Rr = st.columns(2, gap="large")
    with L:
        ui.md("<div class='ex-sec'>CAPABILITY vs SALARY BAND</div>")
        t2 = res.get("t2_demo", []); bands = ["0–3", "3–6", "6–10", "10–15", "15–25", "25–50"]
        if t2:
            f = _fig(280)
            for d, col in zip(t2[:3], [C["blue"], C["grey"], C["teal"]]):
                f.add_trace(go_.Bar(x=bands, y=[100 * p for p in d["probs"]], name=d["title"], marker_color=col))
            f.update_layout(showlegend=True, barmode="group", legend=dict(orientation="h", y=1.15)); f.update_yaxes(title="% probability"); f.update_xaxes(title="LPA band (JD Scanner, illustrative JDs)")
            st.plotly_chart(f, width="stretch", config={"displayModeBar": False}, key="ex_band")
            ui.md("<div class='nd-sub'>Predicted band distributions for sample job descriptions (selected T2 model: 44% exact band, 85% within one band). Distributions, never an exact salary.</div>")
    with Rr:
        ui.md("<div class='ex-sec'>CAPABILITY HEADROOM</div>")
        ui.md("".join(f"<div class='ex-hr'><span>{r['name']}</span><div class='ex-bar'><span style='width:{r['headroom']:.0f}%;background:{C['gold']}'></span></div><b>{r['headroom']:.0f}%</b></div>"
                      for r in sorted(R_, key=lambda r: -r["headroom"])))
        ui.md("<div class='nd-sub'>Share of juniors (JDS) not yet at the 5.0 ceiling. Headroom is necessary, not sufficient — Big Data has the most room but the weakest internal link.</div>")


def data_quality(b):
    cl = b.results.get("cleaning", {}) if b.ok_results else {}
    if not cl: return
    ui.md("<div class='ex-sec'>DATA QUALITY · Analytics_Jobs.csv</div>")
    items = [("Raw records", f"{cl['raw']:,}", "as supplied"), ("Duplicate records", f"{cl['dup']:,}", "exact duplicates removed"),
             ("Truncated skill text", f"{cl['trunc_pct']:.1f}%", "skills field cut off — description text also parsed"),
             ("Missing job type", f"{cl['jobtype_missing_pct']:.1f}%", "field excluded from models"), ("Missing description", f"{cl['desc_missing_raw']:,}", "rows kept; skills field used"),
             ("Off-domain postings", f"{cl['spam']:,}", "non-data roles flagged, kept in 'wide' population"), ("Clean records", f"{cl['clean']:,}", "analysis population")]
    ui.md("<div class='ex-cards ex7'>" + "".join(f"<div class='ex-card'><div class='nd-label'>{a}</div><div class='ex-num' style='font-size:26px'>{v}</div><div class='nd-sub'>{s}</div></div>" for a, v, s in items) + "</div>")
    with st.expander("DATA PREPARATION — how raw postings became analysis features"):
        prev = cl.get("prevalence", {}).get("primary", {})
        ui.md("<table class='nd-tbl'><tr><th>Step</th><th>What we did</th></tr>"
              "<tr><td>Normalised skills</td><td>Regex taxonomy cap-tax-v2.0 maps free-text skills to 7 capability flags (5 shown + Viz, MIS).</td></tr>"
              "<tr><td>Experience bands</td><td>Parsed 'x–y yrs' to min/max/mid; 0 parse failures.</td></tr>"
              "<tr><td>Salary categories</td><td>Six ordered LPA bands: 0–3, 3–6, 6–10, 10–15, 15–25, 25–50.</td></tr>"
              f"<tr><td>Role categories</td><td>Primary data roles ({cl.get('ds_primary', 0):,}) vs wide population ({cl.get('ds_wide', 0):,}).</td></tr>"
              "<tr><td>Capability groups</td><td>Prevalence in primary roles: " + " · ".join(f"{SHORT.get(k, k.upper())} {v:.1f}%" for k, v in prev.items()) + "</td></tr></table>")


def decision_page(b, go):
    R_ = rows(b.results); top = R_[0]; dec = b.results.get("decision", {}); nxt = next((r for r in R_ if r["name"] == dec.get("next") or LABEL.get(r["key"]) == dec.get("next")), R_[1])
    conf = "HIGH" if dec.get("p_beat", 0) >= 0.9 else ("MEDIUM" if dec.get("p_beat", 0) >= 0.8 else "LOW")
    with st.container(key="exdecision"):
        ui.md(f"<div class='nd-kicker' style='color:#F4A259'>NEXUS DECISION</div><div class='nd-label light' style='margin-top:14px;color:#B8C6E4'>TOP PRIORITY</div>"
              f"<div class='ex-title' style='font-size:64px'>{top['name']}</div><div style='margin:6px 0 18px 0'>{dchip(top['decision'])}</div>"
              "<div class='ex-dgrid'>" + "".join(f"<div><div class='nd-label' style='color:#8FA3C9'>{a}</div><div class='ex-dv'>{v}</div><div class='ex-ds'>{s}</div></div>" for a, v, s in [
                  ("INTERNAL SUCCESS", top["li"], f"Cliff's δ {top['delta']:.2f}"), ("MARKET DEMAND", top["lm"], f"odds ratio {top['OR']:.2f}, 6/6 models"),
                  ("HEADROOM", top["lh"], f"{top['headroom']:.0f}% of juniors below ceiling"), ("CONFIDENCE", conf, f"beats {nxt['name']} in {dec.get('p_beat', 0)*100:.1f}% of 1,000 refits")]) + "</div>"
              f"<div class='ex-p' style='margin-top:18px'><b style='color:#fff'>Why?</b> {ui.esc(top['why'])} Modelled gain +{top['Ek']:.1f} pp P(high hike) per +0.5 step [{top['Ek_lo']:.1f}, {top['Ek_hi']:.1f}].</div>")
    ui.md("<div class='ex-sec'>THE FULL DECISION</div><table class='nd-tbl'><tr><th>#</th><th>Capability</th><th>Decision</th><th>Internal</th><th>Market</th><th>Headroom</th><th>Why</th></tr>" + "".join(
        f"<tr><td>{i}</td><td><b>{r['name']}</b></td><td>{dchip(r['decision'])}</td><td>{lchip(r['li'])}</td><td>{lchip(r['lm'])}</td><td>{lchip(r['lh'])}</td><td style='font-size:12px'>{ui.esc(r['why'])}</td></tr>"
        for i, r in enumerate(R_, 1)) + "</table>")
    ui.md("<div class='nd-note'>Association evidence from one company (JDS, n = 139) plus 14,840 market postings — not causal. A human makes the final call; ties are declared, not hidden.</div>")


CSS = """
.st-key-exhero {{ background:radial-gradient(1200px 500px at 85% 40%, #1B2E5C 0%, {navy} 60%); padding:0 !important; animation:exfade .6s ease both; }}
.st-key-exbody > div {{ max-width:1320px; margin:0 auto; padding:0 32px; }}
.st-key-exhero > div {{ max-width:1320px; margin:0 auto; padding:18px 32px 10px 32px; }}
.ex-title {{ font-family:{serif}; color:#fff; font-size:72px; line-height:1; letter-spacing:.02em; margin:8px 0 10px 0; }}
.ex-h2 {{ color:#F5F1E8; font-size:24px; line-height:1.3; max-width:620px; font-family:{serif}; }}
.ex-p {{ color:#B8C6E4; font-size:15px; line-height:1.55; max-width:600px; margin:12px 0 18px 0; }}
.st-key-exhero button[kind="secondary"] {{ background:transparent !important; color:#F5F1E8 !important; border:1px solid #5C6E96 !important; }}
.ex-cards {{ display:grid; grid-template-columns:repeat(5,1fr); gap:12px; margin:22px 0 26px 0; }} .ex-cards.ex7 {{ grid-template-columns:repeat(7,1fr); }}
.ex-card {{ background:#fff; border-radius:12px; padding:16px 16px 14px 16px; box-shadow:0 1px 2px rgba(14,26,51,.06),0 6px 18px rgba(14,26,51,.05); transition:transform .25s, box-shadow .25s; animation:exup .55s ease both; position:relative; }}
.ex-card:hover {{ transform:translateY(-3px); box-shadow:0 2px 4px rgba(14,26,51,.08),0 14px 28px rgba(14,26,51,.09); }}
.ex-ic {{ position:absolute; right:14px; top:12px; color:{saffron}; font-size:16px; opacity:.8; }}
.ex-num {{ font-family:{serif}; font-size:38px; color:{ink}; line-height:1.1; margin:4px 0 2px 0; }}
@property --n {{ syntax:'<integer>'; initial-value:0; inherits:false; }}
.ex-count {{ --n:0; animation:excount 1.4s cubic-bezier(.2,.7,.2,1) forwards; counter-reset:n var(--n); }} .ex-count::after {{ content:counter(n); }}
@keyframes excount {{ to {{ --n:var(--to); }} }}
@keyframes exup {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:none; }} }}
@keyframes exfade {{ from {{ opacity:0; }} to {{ opacity:1; }} }}
@keyframes exgrow {{ from {{ width:0; }} }}
.ex-sec {{ font-size:11px; font-weight:800; letter-spacing:.16em; color:{ink}; margin:22px 0 6px 0; display:flex; align-items:center; gap:8px; }}
.ex-sec::before {{ content:''; width:18px; height:2px; background:{saffron}; display:inline-block; }}
[class*="st-key-exrank_"] {{ background:#fff; border-radius:12px; padding:10px 16px !important; margin-bottom:8px; transition:box-shadow .25s, transform .25s; animation:exup .5s ease both; }}
[class*="st-key-exrank_"]:hover {{ box-shadow:0 10px 24px rgba(14,26,51,.08); transform:translateX(3px); }}
.ex-rk {{ font-family:{serif}; font-size:30px; color:{gold}; }} .ex-nm {{ font-weight:700; font-size:16px; color:{ink}; margin-bottom:4px; }}
.ex-d {{ display:inline-block; font-size:10.5px; font-weight:800; letter-spacing:.14em; border:1.5px solid; border-radius:999px; padding:2px 10px; background:rgba(255,255,255,.9); }}
.ex-bar {{ height:8px; background:#EEE9DD; border-radius:999px; overflow:hidden; margin:2px 0 6px 0; }} .ex-bar span {{ display:block; height:100%; border-radius:999px; animation:exgrow 1.1s cubic-bezier(.2,.7,.2,1) both; }}
.ex-conv {{ background:#fff; border-radius:12px; padding:14px; border-top:3px solid {green}; min-height:330px; animation:exup .5s ease both; transition:transform .25s; }} .ex-conv:hover {{ transform:translateY(-3px); }}
.ex-conv.ex-conflict {{ border-top-color:{gold}; }}
.ex-row {{ display:flex; justify-content:space-between; align-items:center; font-size:12.5px; padding:6px 0; border-bottom:1px solid #F0ECE2; }}
.ex-arrow {{ text-align:center; color:{muted}; font-size:20px; margin:6px 0 4px 0; }}
.ex-l {{ font-size:10px; font-weight:800; letter-spacing:.1em; padding:2px 8px; border-radius:4px; }}
.ex-high {{ background:#DDF0E4; color:#1F6B47; }} .ex-medium {{ background:#F6EBCF; color:#7A5A12; }} .ex-low {{ background:#F3E1D9; color:#8A3A1C; }}
.ex-hr {{ display:grid; grid-template-columns:170px 1fr 44px; gap:10px; align-items:center; font-size:13px; margin:7px 0; }} .ex-hr .ex-bar {{ margin:0; }}
.st-key-exdecision {{ background:radial-gradient(900px 400px at 90% 10%, #1B2E5C 0%, {navy} 65%); border-radius:16px; padding:30px 34px !important; animation:exfade .6s ease both; }}
.ex-dgrid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:18px; border-top:1px solid #2A3D68; padding-top:16px; }}
.ex-dv {{ font-family:{serif}; color:#fff; font-size:28px; }} .ex-ds {{ color:#8FA3C9; font-size:12px; }}
@media (max-width:1100px) {{ .ex-cards, .ex-cards.ex7 {{ grid-template-columns:repeat(2,1fr); }} .ex-title {{ font-size:48px; }} .ex-dgrid {{ grid-template-columns:repeat(2,1fr); }} }}
@media (prefers-reduced-motion: reduce) {{ .ex-card, .ex-bar span, [class*="st-key-exrank_"], .ex-conv {{ animation:none !important; }} }}
"""


def css():
    return CSS.format(navy=C["navy"], serif=ui.SERIF, saffron=C["blue"], ink=C["ink"], gold=C["gold"], green=C["teal"], muted=C["muted"])
