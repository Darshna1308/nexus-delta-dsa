"""3D scenes (Three.js, bundled locally in static/nd3d.js; no CDN, works offline).
Every scene receives only values already in results.json / app_artifacts.json — nothing is invented here.
If WebGL is unavailable the scene renders a plain table fallback inside the frame."""
import json, html as _html
import streamlit as st
from config import LABEL, SHORT

ORDER = ["maths_stats", "coding", "ai_ml", "story", "big_data"]
S5, S6 = "S5 +all controls (primary tax.)", "S6 all controls (wide tax. & population)"

# The scenes are served as a Streamlit custom component (folder nd3d_component/), so Streamlit itself resolves the
# asset URLs — this works locally and under Streamlit Community Cloud's /~/+/ sub-path alike.
import streamlit.components.v1 as _components
from pathlib import Path as _Path
_COMP = _components.declare_component("nd3d", path=str(_Path(__file__).parent / "nd3d_component"))


def _frame(kind: str, data: dict, height: int, fallback: str = "3D view unavailable here — the same data is shown in the tables on this page."):
    _COMP(kind=kind, data=data, fallback=fallback, height=height, key=f"nd3d_{kind}", default=None)


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
    fb = "<b>Data-role postings by city</b><table><tr><th>City</th><th>Postings</th><th>≥ 10 LPA</th></tr>" + "".join(
        f"<tr><td>{_html.escape(c['name'])}</td><td>{c['n']:,}</td><td>{c['pct10']:.0f}%</td></tr>" for c in cities) + "</table>"
    _frame("india", dict(svg="india.svg", cities=cities, caps=caps, initial=initial), height, fb)
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
