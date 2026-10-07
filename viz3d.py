"""3D scenes (Three.js, bundled locally in static/nd3d.js; no CDN, works offline).
Every scene receives only values already in results.json / app_artifacts.json — nothing is invented here.
If WebGL is unavailable the scene renders a plain table fallback inside the frame."""
import json, html as _html
import streamlit as st
from config import LABEL, SHORT

ORDER = ["maths_stats", "coding", "ai_ml", "story", "big_data"]
S5, S6 = "S5 +all controls (primary tax.)", "S6 all controls (wide tax. & population)"

_HEAD = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
@font-face{font-family:'IBM Plex Sans';src:url(/app/static/fonts/ibm-plex-sans-latin-400-normal.woff2) format('woff2');font-weight:400}
@font-face{font-family:'IBM Plex Sans';src:url(/app/static/fonts/ibm-plex-sans-latin-600-normal.woff2) format('woff2');font-weight:600}
@font-face{font-family:'IBM Plex Mono';src:url(/app/static/fonts/ibm-plex-mono-latin-400-normal.woff2) format('woff2');font-weight:400}
html,body{margin:0;height:100%;background:transparent;overflow:hidden} #r{height:100vh;width:100%}
</style></head><body><div id="r"></div><script src="/app/static/nd3d.js"></script>"""


def _frame(kind: str, data: dict, height: int):
    payload = json.dumps(data).replace("</", "<\\/")
    st.iframe(f"{_HEAD}<script>window.ND3D && ND3D.{kind}(document.getElementById('r'), {payload});</script></body></html>", height=height)


def cap_evidence(results: dict) -> list:
    """per-capability evidence exactly as computed by the notebooks (δ, OR S5–S6, S5 CI, headroom, verdict)."""
    M = {m["key"]: m for m in results.get("matrix", [])}; mo = results.get("market_or", {}); dec = results.get("decision", {})
    out = []
    for k in ORDER:
        m = M.get(k)
        if not m or S5 not in mo or k not in mo[S5]: continue
        a, b = mo[S5][k]["OR"], mo[S6][k]["OR"]
        lead = dec.get("lead", "").lower() == m.get("capability", "").lower()
        out.append(dict(key=k, label=LABEL[k], short=SHORT[k], delta=m["delta"], or_s5=a, or_lo=min(a, b), or_hi=max(a, b),
                        ci_lo=mo[S5][k]["lo"], ci_hi=mo[S5][k]["hi"], headroom=m["headroom"], verdict=m["verdict"],
                        conflict=m["verdict"] == "FUND WITH REFRAME", p_beat=dec.get("p_beat") if lead else None))
    return out


def india_map(results: dict, height=470, initial="all"):
    cc = results.get("city_capability")
    caps = cap_evidence(results)
    if not cc or not caps: return False
    cities = [dict(name=n, lon=v["lon"], lat=v["lat"], n=v["n"], pct10=v["pct_ge_10LPA"], caps=v["caps"]) for n, v in sorted(cc.items(), key=lambda x: -x[1]["n"])]
    _frame("india", dict(svg="/app/static/india.svg", cities=cities, caps=caps, initial=initial), height)
    return True


def evidence_landscape(results: dict, height=470, initial=None):
    caps = cap_evidence(results)
    if not caps: return False
    _frame("landscape", dict(caps=caps, initial=initial), height); return True


def market_landscape(art: dict, height=420):
    rp = (art or {}).get("roles") or (art or {}).get("role_profiles") or {}
    roles = [dict(name=r, n=v["n_postings"], share=v["band_share"]) for r, v in rp.items() if v.get("band_share")]
    if not roles: return False
    _frame("market", dict(roles=roles, bands=["0–3", "3–6", "6–10", "10–15", "15–25", "25–50"]), height); return True


def development_path(plan: list, height=360):
    if not plan: return False
    _frame("path", dict(steps=[dict(cap=SHORT.get(p["key"], p["capability"]), tier=p["tier"], why=p["why"]) for p in plan]), height); return True


def evidence_pipeline(results: dict, height=380):
    cl = results.get("cleaning", {})
    nodes = [dict(id="aj", kind="data", label="Analytics Jobs", sub=f"{cl.get('raw', 15841):,} → {cl.get('clean', 14840):,}", x=-3.6, z=-1.6),
             dict(id="ds", kind="data", label="Data Science Jobs", sub="1,602 rows", x=-3.6, z=-0.5),
             dict(id="jds", kind="data", label="JDS skills", sub="n = 139", x=-3.6, z=0.6),
             dict(id="sds", kind="data", label="SDS traits", sub="n = 161", x=-3.6, z=1.7),
             dict(id="tax", kind="hub", label="Capability taxonomy", sub="cap-tax-v2.0", x=-1.0, z=0.05),
             dict(id="int", kind="signal", label="Internal evidence", sub="Cliff's δ", x=1.3, z=-1.9),
             dict(id="mkt", kind="signal", label="Market evidence", sub="odds ratio × 6", x=1.3, z=0.0),
             dict(id="hr", kind="signal", label="Headroom", sub="E_k · bootstrap", x=1.3, z=1.9),
             dict(id="dec", kind="decision", label="Decision", sub="3 verdicts", x=4.0, z=0.0)]
    links = [["aj", "tax"], ["ds", "tax"], ["jds", "tax"], ["sds", "tax"], ["tax", "int"], ["tax", "mkt"], ["tax", "hr"], ["int", "dec"], ["mkt", "dec"], ["hr", "dec"]]
    _frame("pipeline", dict(nodes=nodes, links=links), height); return True
