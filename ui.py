"""UI shell: CSS, top navigation, hero, chips, stat blocks, provenance badges, footer. Pure presentation — no analytics."""
import html
import streamlit as st
import config
from config import C, BRAND, PAGES, PROV, EVIDENCE_LABELS

SERIF = "'Iowan Old Style', 'Palatino Linotype', Palatino, Georgia, serif"
SANS = "Inter, 'Segoe UI', system-ui, -apple-system, Roboto, sans-serif"


def css(active_page: str, selected_cap: str = None) -> str:
    nav_active = "".join(f".st-key-nav_{i} button{{color:#fff !important;border-bottom:2px solid {C['blue']} !important;}}" for i, p in enumerate(PAGES) if p == active_page)
    sel = f".st-key-row_{selected_cap}{{background:{C['blue_soft']};border-left:3px solid {C['blue']} !important;}}" if selected_cap else ""
    return f"""<style>
html, body, [class*="css"], .stApp {{ font-family:{SANS}; color:{C['ink']}; }}
.stApp {{ background:{C['paper']}; }}
#MainMenu, footer, header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] {{ display:none !important; visibility:hidden; }}
.block-container, [data-testid="stMainBlockContainer"] {{ padding:0 !important; max-width:100% !important; }}
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] {{ gap:0 !important; }}
[data-testid="stAppViewContainer"], section.main, [data-testid="stMain"] {{ padding-top:0 !important; margin-top:0 !important; }}
[data-testid="stAppViewContainer"] > .main > div {{ padding-top:0; }}
/* shell */
.st-key-shell {{ background:{C['navy']}; padding:0 !important; border-bottom:1px solid {C['navy3']}; }}
.st-key-shell > div {{ max-width:1320px; margin:0 auto; padding:8px 32px 0 32px; gap:0 !important; }}
.nd-brand {{ color:#fff; font-weight:700; letter-spacing:.14em; font-size:15px; line-height:1.1; }}
.nd-brand small {{ display:block; color:#8FA3C9; font-weight:500; letter-spacing:.05em; font-size:9.5px; margin-top:3px; white-space:nowrap; }}
.nd-corner {{ text-align:right; color:#8FA3C9; font-size:10px; line-height:1.4; letter-spacing:.03em; white-space:nowrap; }}
.nd-corner b {{ color:#fff; letter-spacing:.12em; font-size:11px; }}
[class*="st-key-nav_"] button {{ background:transparent !important; border:none !important; border-bottom:2px solid transparent !important; border-radius:0 !important; color:#9DB0D6 !important;
   font-size:11px !important; font-weight:600 !important; letter-spacing:.07em !important; padding:10px 4px !important; min-height:0 !important; box-shadow:none !important; }}
[class*="st-key-nav_"] button:hover {{ color:#fff !important; }}
[class*="st-key-nav_"] button p {{ font-size:11px !important; font-weight:600 !important; letter-spacing:.07em; white-space:nowrap; overflow:visible !important; text-overflow:clip !important; }}
{nav_active}
/* hero */
.st-key-hero {{ background:{C['navy']}; background-image:radial-gradient(1200px 400px at 85% -20%, rgba(47,107,255,.22), transparent 60%); padding:0 !important; }}
.st-key-hero > div {{ max-width:1320px; margin:0 auto; padding:34px 32px 38px 32px; }}
.nd-kicker {{ color:{C['teal']}; font-size:11px; font-weight:700; letter-spacing:.16em; text-transform:uppercase; }}
.nd-hero h1 {{ font-family:{SERIF}; color:#fff; font-weight:500; font-size:56px; line-height:1.04; letter-spacing:-.015em; margin:8px 0 10px 0; padding:0; }}
.nd-hero h1 em {{ color:#7FA6FF; font-style:normal; }}
.nd-hero p {{ color:#B8C6E4; font-size:16px; max-width:760px; line-height:1.5; margin:0; }}
.nd-page-h {{ font-family:{SERIF}; font-weight:500; font-size:38px; line-height:1.08; letter-spacing:-.01em; color:{C['ink']}; margin:2px 0 4px 0; }}
.nd-q {{ color:{C['muted']}; font-size:15px; margin:0 0 14px 0; }}
.nd-body {{ max-width:1320px; margin:0 auto; padding:22px 32px 8px 32px; }}
.st-key-body > div {{ max-width:1320px; margin:0 auto; padding:22px 32px 8px 32px; }}
/* cards */
[class*="st-key-card"] {{ background:{C['card']}; border:1px solid {C['line']}; border-radius:6px; padding:16px 18px; }}
[class*="st-key-dark"] {{ background:{C['navy']}; border-radius:6px; padding:16px 18px; color:#E9EEF9; }}
[class*="st-key-row_"] {{ border-bottom:1px solid {C['line']}; border-left:3px solid transparent; padding:6px 8px; }}
{sel}
.nd-label {{ font-size:10.5px; font-weight:700; letter-spacing:.12em; text-transform:uppercase; color:{C['muted']}; margin-bottom:3px; }}
.nd-label.light {{ color:#8FA3C9; }}
.nd-val {{ font-family:{SERIF}; font-size:30px; line-height:1.1; color:{C['ink']}; font-weight:500; }}
.nd-val.s {{ font-size:22px; }}
.nd-sub {{ font-size:12px; color:{C['muted']}; margin-top:3px; line-height:1.35; }}
.nd-chip {{ display:inline-block; font-size:10.5px; font-weight:700; letter-spacing:.07em; padding:3px 8px; border-radius:3px; white-space:nowrap; }}
.nd-hbar {{ height:6px; background:#E6E2D8; border-radius:3px; margin-top:6px; }} .nd-hbar > span {{ display:block; height:6px; border-radius:3px; background:{C['blue']}; }}
.nd-note {{ font-size:12px; color:{C['muted']}; border-left:2px solid {C['line']}; padding-left:10px; margin:6px 0; line-height:1.45; }}
.nd-warn {{ font-size:12.5px; color:#7A4B00; background:{C['amber_soft']}; border-left:3px solid {C['amber']}; padding:8px 12px; margin:6px 0; line-height:1.45; }}
.nd-err {{ font-size:12.5px; color:#7A1F10; background:{C['red_soft']}; border-left:3px solid {C['red']}; padding:8px 12px; margin:6px 0; line-height:1.45; }}
.nd-action {{ background:{C['navy']}; color:#fff; padding:12px 14px; border-radius:4px; font-size:13.5px; line-height:1.45; margin-top:8px; }} .nd-action b {{ color:#7FA6FF; letter-spacing:.08em; font-size:10.5px; display:block; margin-bottom:3px; }}
.nd-tbl {{ width:100%; border-collapse:collapse; font-size:12.5px; }} .nd-tbl th {{ text-align:left; font-size:10.5px; letter-spacing:.1em; text-transform:uppercase; color:{C['muted']}; border-bottom:1.5px solid {C['ink']}; padding:6px 8px; }}
.nd-tbl td {{ border-bottom:1px solid {C['line']}; padding:8px; vertical-align:top; line-height:1.4; }}
.nd-dnarow {{ display:grid; grid-template-columns:150px 1fr 120px; gap:12px; align-items:center; padding:7px 0; border-bottom:1px solid {C['line']}; font-size:12.5px; }}
.nd-dnarow .bar {{ font-family:ui-monospace, Menlo, Consolas, monospace; font-size:11px; line-height:1.5; letter-spacing:.02em; }}
.nd-progress {{ height:3px; background:#DAD6CB; margin:4px 0 14px 0; }} .nd-progress > span {{ display:block; height:3px; background:{C['blue']}; }}
.nd-foot {{ border-top:1px solid {C['line']}; margin-top:28px; padding:16px 0 26px 0; color:{C['muted']}; font-size:11px; letter-spacing:.05em; display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px; }}
.st-key-demobar {{ background:{C['blue']}; padding:0 !important; }}
.st-key-demobar > div {{ max-width:1320px; margin:0 auto; padding:8px 32px; }}
.st-key-demobar button {{ background:rgba(255,255,255,.14) !important; border:1px solid rgba(255,255,255,.55) !important; color:#fff !important; min-height:34px; }}
.st-key-demobar button:disabled {{ opacity:.4; }}
.st-key-demobar button p {{ color:#fff !important; font-size:11px !important; letter-spacing:.08em; font-weight:700; }}
/* streamlit controls */
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] {{ background:{C['blue']}; border:1px solid {C['blue']}; color:#fff; border-radius:4px; font-weight:600; letter-spacing:.03em; }}
.stButton > button[kind="secondary"], .stButton > button[data-testid="stBaseButton-secondary"] {{ border-radius:4px; border:1px solid {C['ink']}; background:transparent; color:{C['ink']}; font-weight:600; }}
[class*="st-key-caplink"] button {{ border:none !important; background:transparent !important; text-align:left !important; padding:2px 0 !important; justify-content:flex-start !important; font-weight:700 !important; color:{C['ink']} !important; }}
[class*="st-key-caplink"] button p {{ font-size:14px !important; font-weight:700 !important; }}
[class*="st-key-tile_"] button {{ border:none !important; background:transparent !important; padding:0 !important; color:{C['blue']} !important; font-size:11px !important; font-weight:700 !important; letter-spacing:.08em; justify-content:flex-start !important; min-height:0 !important; }}
[class*="st-key-tile_"] button p {{ font-size:11px !important; letter-spacing:.08em; }}
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {{ background:#fff !important; border:1px solid {C['line']} !important; border-radius:6px !important; color:{C['ink']} !important; min-height:42px; }}
[data-testid="stTextInput"] > div > div, [data-testid="stTextInput"] [data-baseweb="input"] {{ background:#fff !important; border:1px solid #C9C5B8 !important; border-radius:6px !important; }}
[data-testid="stTextInput"] label p {{ font-size:11px !important; font-weight:700 !important; letter-spacing:.08em; text-transform:uppercase; color:{C['muted']} !important; }}
.st-key-shell {{ min-height:56px; }}
.st-key-logout {{ text-align:right; }} .st-key-logout button {{ color:#9DB0D6 !important; padding:0 !important; min-height:18px !important; border:none !important; background:transparent !important; }} .st-key-logout button p {{ font-size:10px !important; font-weight:700 !important; letter-spacing:.1em; }} .st-key-logout button:hover {{ color:#fff !important; }}
.st-key-body h2, .st-key-body h3 {{ font-family:{SERIF}; font-weight:500; }}
[data-testid="stPopover"] button {{ padding:0 8px !important; min-height:0 !important; height:22px !important; font-size:10.5px !important; font-weight:700 !important; letter-spacing:.07em; border-radius:3px !important; width:auto !important; }}
[data-testid="stPopover"] button p {{ font-size:10.5px !important; white-space:nowrap !important; overflow:visible !important; text-overflow:clip !important; }}
[data-testid="stPopover"] {{ width:auto !important; }}
.nd-chip {{ letter-spacing:.04em; }}
.stTabs [data-baseweb="tab"] {{ font-size:12px; font-weight:700; letter-spacing:.08em; }}
@media (max-width:1100px) {{ .nd-hero h1 {{ font-size:40px; }} .nd-page-h {{ font-size:30px; }} .nd-dnarow {{ grid-template-columns:110px 1fr 100px; }} }}
@media (max-width:760px) {{ .st-key-shell > div, .st-key-hero > div, .st-key-body > div {{ padding-left:14px; padding-right:14px; }} .nd-hero h1 {{ font-size:32px; }} }}
</style>"""


def md(h: str): st.markdown(h, unsafe_allow_html=True)


def esc(s) -> str: return html.escape(str(s))


def chip(text: str, kind: str = "grey") -> str:
    palette = {"teal": (C["teal_soft"], "#0A6B5F"), "blue": (C["blue_soft"], "#1C47B3"), "amber": (C["amber_soft"], "#7A4B00"), "red": (C["red_soft"], "#8A2A17"), "grey": ("#E9E6DD", C["muted"]), "navy": (C["navy"], "#FFFFFF"), "ink": (C["ink"], "#FFFFFF")}
    bg, fg = palette.get(kind, palette["grey"])
    return f"<span class='nd-chip' style='background:{bg};color:{fg}'>{esc(text)}</span>"


VERDICT_KIND = {"FUND": "teal", "FUND WITH REFRAME": "amber", "TIED": "blue", "DEPRIORITISE": "red", "MONITOR": "grey", "INSUFFICIENT EVIDENCE": "grey", "NO VERDICT SHOWN": "grey"}
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
        with c0: md("<div class='nd-brand'>NEXUS DELTA<small>EVIDENCE-FIRST CAPABILITY DECISIONS</small></div>")
        with c1:
          if show_nav:
            cols = st.columns([0.8, 2.15, 2.0, 1.25, 1.1, 1.0, 1.0, 0.8])
            labels = {"HOME": "HOME", "CAPABILITY INTELLIGENCE": "CAPABILITY INTELLIGENCE", "CAREER INTELLIGENCE": "CAREER INTELLIGENCE", "JD SCANNER": "JD SCANNER", "WORK DNA": "WORK DNA", "CULTURE": "CULTURE", "EVIDENCE": "EVIDENCE", "ABOUT": "ABOUT"}
            for i, (col, p) in enumerate(zip(cols, PAGES)):
                with col: st.button(labels[p], key=f"nav_{i}", on_click=go, args=(p,), type="tertiary")
        with c2:
            md(f"<div class='nd-corner'><b>NEXUS DELTA</b> · Team DSA<br>{account or 'Chandigarh University · Build For Bharat 2.0'}</div>")
            if on_logout: st.button("SIGN OUT", key="logout", on_click=on_logout, type="tertiary")
