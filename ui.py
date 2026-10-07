"""UI shell: CSS, top navigation, hero, chips, stat blocks, provenance badges, footer. Pure presentation — no analytics."""
import html
import streamlit as st
import config
from config import C, BRAND, PAGES, PROV, EVIDENCE_LABELS

SANS = "'IBM Plex Sans', 'Segoe UI', system-ui, -apple-system, sans-serif"
MONO = "'IBM Plex Mono', ui-monospace, Menlo, Consolas, monospace"
SERIF = SANS   # kept for backward compatibility: headings now use IBM Plex Sans (no display serif)


def css(active_page: str, selected_cap: str = None) -> str:
    nav_active = "".join(f".st-key-nav_{i} button{{color:#fff !important;border-bottom:2px solid {C['blue']} !important;}}" for i, p in enumerate(PAGES) if p == active_page)
    sel = f".st-key-row_{selected_cap}{{background:{C['blue_soft']};border-left:3px solid {C['blue']} !important;}}" if selected_cap else ""
    return f"""<style>
html, body, [class*="css"], .stApp {{ font-family:{SANS}; color:{C['ink']}; }}
.stApp {{ background:{C['paper']}; }}
.num, .mono {{ font-family:{MONO}; font-feature-settings:"tnum" 1; }}
#MainMenu, footer, header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] {{ display:none !important; visibility:hidden; }}
.block-container, [data-testid="stMainBlockContainer"] {{ padding:0 !important; max-width:100% !important; }}
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] {{ gap:0 !important; }}
[data-testid="stAppViewContainer"], section.main, [data-testid="stMain"] {{ padding-top:0 !important; margin-top:0 !important; }}
[data-testid="stAppViewContainer"] > .main > div {{ padding-top:0; }}
*:focus-visible {{ outline:2px solid {C['blue']} !important; outline-offset:2px; }}
/* shell: deep indigo structure */
.st-key-shell {{ background:{C['navy']}; padding:0 !important; border-bottom:1px solid {C['navy3']}; min-height:56px; }}
.st-key-shell > div {{ max-width:1320px; margin:0 auto; padding:8px 32px 0 32px; gap:0 !important; }}
.nd-brand {{ color:#F6F3EC; font-weight:600; letter-spacing:.08em; font-size:15px; line-height:1.1; }}
.nd-brand small {{ display:block; color:#A9B8C8; font-weight:400; letter-spacing:.02em; font-size:10.5px; margin-top:3px; white-space:nowrap; }}
.nd-corner {{ text-align:right; color:#A9B8C8; font-size:10.5px; line-height:1.4; white-space:nowrap; }}
.nd-corner b {{ color:#F6F3EC; letter-spacing:.06em; font-size:11px; font-weight:600; }}
[class*="st-key-nav_"] button {{ background:transparent !important; border:none !important; border-bottom:2px solid transparent !important; border-radius:0 !important; color:#C3CED9 !important;
   font-size:13px !important; font-weight:500 !important; letter-spacing:.01em !important; padding:10px 4px !important; min-height:0 !important; box-shadow:none !important; transition:color .2s, border-color .2s; }}
[class*="st-key-nav_"] button:hover {{ color:#fff !important; }}
[class*="st-key-nav_"] button p {{ font-size:13px !important; font-weight:500 !important; letter-spacing:.01em; white-space:nowrap; overflow:visible !important; text-overflow:clip !important; }}
{nav_active}
/* page hero (non-home pages) on ivory */
.st-key-hero {{ background:{C['paper']}; padding:0 !important; border-bottom:1px solid {C['line']}; }}
.st-key-hero > div {{ max-width:1320px; margin:0 auto; padding:30px 32px 30px 32px; }}
.nd-kicker {{ color:{C['teal']}; font-size:11.5px; font-weight:600; letter-spacing:.08em; text-transform:uppercase; }}
.nd-hero h1 {{ font-family:{SANS}; color:{C['navy']}; font-weight:600; font-size:38px; line-height:1.15; letter-spacing:-.01em; margin:8px 0 10px 0; padding:0; }}
.nd-hero h1 em {{ color:{C['blue']}; font-style:normal; }}
.nd-hero p {{ color:{C['muted']}; font-size:16px; max-width:760px; line-height:1.55; margin:0; }}
.nd-page-h {{ font-family:{SANS}; font-weight:600; font-size:30px; line-height:1.2; letter-spacing:-.01em; color:{C['navy']}; margin:2px 0 6px 0; }}
.nd-q {{ color:{C['muted']}; font-size:15.5px; margin:0 0 16px 0; max-width:880px; line-height:1.5; }}
.nd-body {{ max-width:1320px; margin:0 auto; padding:22px 32px 8px 32px; }}
.st-key-body > div {{ max-width:1320px; margin:0 auto; padding:24px 32px 8px 32px; }}
/* surfaces: quiet, thin borders, almost no shadow */
[class*="st-key-card"] {{ background:{C['card']}; border:1px solid {C['line']}; border-radius:8px; padding:16px 18px; transition:border-color .2s; }}
[class*="st-key-card"]:hover {{ border-color:#CBBFA9; }}
[class*="st-key-dark"] {{ background:{C['navy']}; border-radius:8px; padding:16px 18px; color:#E9EEF3; }}
[class*="st-key-row_"] {{ border-bottom:1px solid {C['line']}; border-left:3px solid transparent; padding:6px 8px; transition:background .2s; }}
{sel}
.nd-label {{ font-size:11px; font-weight:600; letter-spacing:.06em; text-transform:uppercase; color:{C['muted']}; margin-bottom:4px; }}
.nd-label.light {{ color:#A9B8C8; }}
.nd-val {{ font-family:{MONO}; font-size:26px; line-height:1.15; color:{C['navy']}; font-weight:500; font-feature-settings:"tnum" 1; }}
.nd-val.s {{ font-family:{SANS}; font-size:19px; font-weight:600; }}
.nd-sub {{ font-size:12.5px; color:{C['muted']}; margin-top:3px; line-height:1.45; }}
.nd-chip {{ display:inline-block; font-size:11px; font-weight:600; letter-spacing:.03em; padding:3px 8px; border-radius:4px; white-space:nowrap; }}
.nd-hbar {{ height:6px; background:#E7E1D5; border-radius:3px; margin-top:6px; }} .nd-hbar > span {{ display:block; height:6px; border-radius:3px; background:{C['teal']}; }}
.nd-note {{ font-size:12.5px; color:{C['muted']}; border-left:2px solid {C['line']}; padding-left:10px; margin:6px 0; line-height:1.5; }}
.nd-warn {{ font-size:13px; color:#6B4A0E; background:{C['amber_soft']}; border-left:3px solid {C['amber']}; padding:8px 12px; margin:6px 0; line-height:1.5; }}
.nd-err {{ font-size:13px; color:#6E2A17; background:{C['red_soft']}; border-left:3px solid {C['red']}; padding:8px 12px; margin:6px 0; line-height:1.5; }}
.nd-action {{ background:{C['navy']}; color:#F6F3EC; padding:12px 14px; border-radius:6px; font-size:13.5px; line-height:1.5; margin-top:8px; }} .nd-action b {{ color:#E8B98F; letter-spacing:.06em; font-size:11px; display:block; margin-bottom:3px; }}
.nd-tbl {{ width:100%; border-collapse:collapse; font-size:13px; }} .nd-tbl th {{ text-align:left; font-size:11px; font-weight:600; letter-spacing:.05em; text-transform:uppercase; color:{C['muted']}; border-bottom:1.5px solid {C['navy']}; padding:6px 8px; }}
.nd-tbl td {{ border-bottom:1px solid {C['line']}; padding:8px; vertical-align:top; line-height:1.45; }}
.nd-dnarow {{ display:grid; grid-template-columns:150px 1fr 120px; gap:12px; align-items:center; padding:7px 0; border-bottom:1px solid {C['line']}; font-size:13px; }}
.nd-dnarow .bar {{ font-family:{MONO}; font-size:11px; line-height:1.5; }}
.nd-progress {{ height:3px; background:#DDD5C6; margin:4px 0 14px 0; }} .nd-progress > span {{ display:block; height:3px; background:{C['blue']}; transition:width .45s ease; }}
.nd-foot {{ border-top:1px solid {C['line']}; margin-top:32px; padding:16px 0 26px 0; color:{C['muted']}; font-size:12px; display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px; }}
.st-key-demobar {{ background:{C['blue']}; padding:0 !important; }}
.st-key-demobar > div {{ max-width:1320px; margin:0 auto; padding:8px 32px; }}
.st-key-demobar button {{ background:rgba(255,255,255,.14) !important; border:1px solid rgba(255,255,255,.6) !important; color:#fff !important; min-height:34px; }}
.st-key-demobar button:disabled {{ opacity:.4; }}
.st-key-demobar button p {{ color:#fff !important; font-size:12px !important; font-weight:600; }}
/* streamlit controls: terracotta = action */
.stButton > button {{ transition:background .2s, border-color .2s, color .2s; }}
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] {{ background:{C['blue']}; border:1px solid {C['blue']}; color:#fff; border-radius:6px; font-weight:600; }}
.stButton > button[kind="primary"]:hover {{ background:#B46A36; border-color:#B46A36; }}
.stButton > button[kind="secondary"], .stButton > button[data-testid="stBaseButton-secondary"] {{ border-radius:6px; border:1px solid #BFB4A0; background:transparent; color:{C['navy']}; font-weight:500; }}
.stButton > button[kind="secondary"]:hover {{ border-color:{C['navy']}; color:{C['navy']}; }}
[class*="st-key-caplink"] button {{ border:none !important; background:transparent !important; text-align:left !important; padding:2px 0 !important; justify-content:flex-start !important; font-weight:600 !important; color:{C['navy']} !important; }}
[class*="st-key-caplink"] button p {{ font-size:14px !important; font-weight:600 !important; }}
[class*="st-key-tile_"] button {{ border:none !important; background:transparent !important; padding:0 !important; color:{C['blue']} !important; font-size:12px !important; font-weight:600 !important; justify-content:flex-start !important; min-height:0 !important; }}
[class*="st-key-tile_"] button p {{ font-size:12px !important; }}
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {{ background:#fff !important; border:1px solid {C['line']} !important; border-radius:6px !important; color:{C['ink']} !important; min-height:42px; }}
[data-testid="stTextInput"] > div > div, [data-testid="stTextInput"] [data-baseweb="input"] {{ background:#fff !important; border:1px solid #CBBFA9 !important; border-radius:6px !important; }}
[data-testid="stTextInput"] label p {{ font-size:12px !important; font-weight:600 !important; letter-spacing:.03em; color:{C['muted']} !important; }}
[data-testid="stPopoverBody"] [class*="st-key-nav_"] button {{ color:{C['ink']} !important; border:none !important; justify-content:flex-start !important; padding:8px 10px !important; }}
[data-testid="stPopoverBody"] [class*="st-key-nav_"] button:hover {{ background:{C['blue_soft']} !important; }}
[data-testid="stPopoverBody"] [class*="st-key-nav_"] button p {{ font-size:13px !important; letter-spacing:0 !important; text-transform:none; }}
.st-key-logout {{ text-align:right; }} .st-key-logout button {{ color:#C3CED9 !important; padding:0 !important; min-height:18px !important; border:none !important; background:transparent !important; }} .st-key-logout button p {{ font-size:11px !important; font-weight:600 !important; letter-spacing:.04em; }} .st-key-logout button:hover {{ color:#fff !important; }}
.st-key-body h2, .st-key-body h3 {{ font-family:{SANS}; font-weight:600; color:{C['navy']}; }}
[data-testid="stPopover"] button {{ padding:0 8px !important; min-height:0 !important; height:22px !important; font-size:11px !important; font-weight:600 !important; border-radius:4px !important; width:auto !important; }}
[data-testid="stPopover"] button p {{ font-size:11px !important; white-space:nowrap !important; overflow:visible !important; text-overflow:clip !important; }}
[data-testid="stPopover"] {{ width:auto !important; }}
.stTabs [data-baseweb="tab"] {{ font-size:13px; font-weight:600; }}
[data-testid="stIFrame"], iframe {{ border:none !important; }}
@keyframes ndfade {{ from {{ opacity:0; transform:translateY(4px); }} to {{ opacity:1; transform:none; }} }}
.st-key-body > div {{ animation:ndfade .42s ease both; }}
@media (max-width:1100px) {{ .nd-hero h1 {{ font-size:32px; }} .nd-page-h {{ font-size:26px; }} .nd-dnarow {{ grid-template-columns:110px 1fr 100px; }} }}
@media (max-width:640px) {{
  .st-key-shell [data-testid="stHorizontalBlock"] [data-testid="stHorizontalBlock"] {{ flex-wrap:nowrap !important; overflow-x:auto; gap:2px !important; scrollbar-width:none; }}
  .st-key-shell [data-testid="stHorizontalBlock"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{ min-width:auto !important; width:auto !important; flex:0 0 auto !important; }}
  .nd-corner {{ display:none; }}
}}
@media (max-width:760px) {{ .st-key-shell > div, .st-key-hero > div, .st-key-body > div {{ padding-left:16px; padding-right:16px; }} .nd-hero h1 {{ font-size:26px; }} .nd-page-h {{ font-size:23px; }} }}
@media (prefers-reduced-motion: reduce) {{ *, *::before, *::after {{ animation:none !important; transition:none !important; }} }}
</style>"""


def md(h: str): st.markdown(h, unsafe_allow_html=True)


def esc(s) -> str: return html.escape(str(s))


def chip(text: str, kind: str = "grey") -> str:
    palette = {"teal": (C["teal_soft"], "#234A4E"), "green": (C["green_soft"], "#3F5E45"), "blue": (C["indigo_soft"], C["navy"]), "terracotta": (C["blue_soft"], "#8A4A1C"), "amber": (C["amber_soft"], "#6B4A0E"), "red": (C["red_soft"], "#7A2E1C"), "grey": ("#ECE7DD", "#4F5961"), "navy": (C["navy"], "#FFFFFF"), "ink": (C["ink"], "#FFFFFF")}
    bg, fg = palette.get(kind, palette["grey"])
    return f"<span class='nd-chip' style='background:{bg};color:{fg}'>{esc(text)}</span>"


VERDICT_KIND = {"FUND": "green", "FUND WITH REFRAME": "terracotta", "TIED": "blue", "DEPRIORITISE": "red", "MONITOR": "grey", "INSUFFICIENT EVIDENCE": "grey", "NO VERDICT SHOWN": "grey"}
STATUS_KIND = {"STRONG FIT": "teal", "WATCH": "amber", "HIGH FRICTION": "red", "VERIFY": "grey", "STRONG ALIGNMENT": "teal", "DISCUSSION AREA": "amber", "POTENTIAL FRICTION": "red"}
LEVEL_KIND = {"LOW FRICTION": "teal", "MODERATE FRICTION": "amber", "HIGH FRICTION": "red", "UNDETERMINED": "grey"}
TIER_KIND = {"HIGH PRIORITY": "red", "STRATEGIC": "blue", "STRENGTHEN": "amber", "MAINTAIN": "teal", "LOW EVIDENCE": "grey"}


def verdict_chip(v): return chip(v, VERDICT_KIND.get(v, "grey"))
def signal_chip(txt):
    kind = {"Strong": "teal", "Moderate": "amber", "Weak": "red", "Premium": "teal", "Discount": "red", "Discounted": "red", "Neutral": "grey", "High": "teal", "Low": "red", "Agree": "teal", "Conflict": "red", "Unsupported": "grey"}.get(txt, "grey")
    return chip({"Discount": "Discounted"}.get(txt, txt), kind)


def evidence_chip(label: str) -> str:
    return chip(label, {"OBSERVED": "teal", "DERIVED": "blue", "INFERRED": "amber", "PROPOSED": "red", "SIMULATED": "grey", "ASSUMED": "grey"}.get(label, "grey"))


def stat(label, value, sub="", small=False, light=False):
    md(f"<div class='nd-label{' light' if light else ''}'>{esc(label)}</div><div class='nd-val{' s' if small else ''}'" + (f" style='color:#fff'" if light else "") + f">{value}</div>" + (f"<div class='nd-sub'{' style=\"color:#8FA3C9\"' if light else ''}>{sub}</div>" if sub else ""))


def prov(key: str, key_suffix: str = ""):
    """judge-facing provenance badge: a small popover button labelled with the evidence label; click for source file · notebook · JSON key · method · limitation."""
    p = PROV.get(key)
    if not p: return
    with st.popover(p["label"], key=f"prov_{key}_{key_suffix}"):
        meaning = EVIDENCE_LABELS.get(p["label"], ("", ""))[0]
        md(f"<div class='nd-label'>Evidence label</div>{evidence_chip(p['label'])} <span style='font-size:12px;color:{C['muted']}'>{esc(meaning)}</span>"
           f"<div class='nd-label' style='margin-top:10px'>Source file</div><div style='font-size:13px'>{esc(p['file'])}</div>"
           f"<div class='nd-label' style='margin-top:8px'>Notebook</div><div style='font-size:13px'>{esc(config.NB.get(p['nb'], p['nb']))}</div>"
           f"<div class='nd-label' style='margin-top:8px'>Result JSON key</div><div style='font-size:13px;font-family:ui-monospace,Menlo,monospace'>{esc(p['key'])}</div>"
           f"<div class='nd-label' style='margin-top:8px'>Method</div><div style='font-size:13px'>{esc(p['method'])}</div>"
           f"<div class='nd-label' style='margin-top:8px'>Limitation</div><div style='font-size:13px'>{esc(p['limit'])}</div>")


def header(question_h: str, sub: str = "", kicker: str = ""):
    md(f"<div class='nd-kicker' style='color:{C['blue']}'>{esc(kicker)}</div><div class='nd-page-h'>{esc(question_h)}</div><div class='nd-q'>{esc(sub)}</div>")


def hero(kicker: str, headline_html: str, sub: str = ""):
    with st.container(key="hero"):
        md(f"<div class='nd-hero'><div class='nd-kicker'>{esc(kicker)}</div><h1>{headline_html}</h1>" + (f"<p>{sub}</p>" if sub else "") + "</div>")


def warn(msg): md(f"<div class='nd-warn'>{esc(msg)}</div>")
def err(msg): md(f"<div class='nd-err'>{esc(msg)}</div>")
def note(msg): md(f"<div class='nd-note'>{msg}</div>")


def footer():
    md(f"<div class='nd-foot'><span><b style='color:{C['ink']}'>NEXUS DELTA</b> · BUILD FOR BHARAT 2.0 · CHANDIGARH UNIVERSITY</span><span>TEAM DSA — {' · '.join(BRAND['members'])}</span>"
       f"<span>Offline · no remote API · every number traces to results.json</span></div>")


def shell(active: str, go, account: str = "", on_logout=None, show_nav: bool = True):
    """top bar: brand + nav + corner credits. go(page) is a callback factory."""
    with st.container(key="shell"):
        c0, c1, c2 = st.columns([1.6, 6.0, 1.9], vertical_alignment="center")
        with c0: md("<div class='nd-brand'>NEXUS DELTA<small>Evidence-first capability decisions</small></div>")
        with c1:
          if show_nav:
            from config import TOP_N
            labels = {"HOME": "Overview", "EVIDENCE": "Evidence", "CAPABILITY INTELLIGENCE": "Capabilities", "INSIGHTS": "Insights", "DECISION": "Decision", "CAREER INTELLIGENCE": "Career Intelligence",
                      "JD SCANNER": "JD Scanner", "WORK DNA": "Work DNA", "CULTURE": "Culture", "ABOUT": "About"}
            cols = st.columns([1.1, 1.0, 1.2, 1.0, 1.0, 1.0, 2.2])
            for i, p in enumerate(PAGES[:TOP_N]):
                with cols[i]: st.button(labels[p], key=f"nav_{i}", on_click=go, args=(p,), type="tertiary")
            with cols[TOP_N], st.popover("More ▾" if active not in PAGES[TOP_N:] else labels[active] + " ▾", key="nav_more"):
                for i, p in enumerate(PAGES[TOP_N:], TOP_N): st.button(labels[p], key=f"nav_{i}", on_click=go, args=(p,), width="stretch")
        with c2:
            md(f"<div class='nd-corner'><b>NEXUS DELTA</b> · Team DSA<br>{account or 'Chandigarh University · Build For Bharat 2.0'}</div>")
            if on_logout: st.button("Sign out", key="logout", on_click=on_logout, type="tertiary")
