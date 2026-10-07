"""Plotly figures in the NEXUS DELTA visual language (thin lines, navy ink, electric-blue primary, teal secondary). All figures take already-loaded data."""
import math
import plotly.graph_objects as go
import config
from config import C, LABEL, SHORT

FONT = dict(family="'IBM Plex Sans', 'Segoe UI', system-ui, sans-serif", color=C["ink"], size=12)
VERDICT_COLOR = {"FUND": C["green"], "FUND WITH REFRAME": C["blue"], "TIED": C["gold"], "DEPRIORITISE": C["grey"], "MONITOR": C["grey"], "INSUFFICIENT EVIDENCE": C["grey"]}
BANDS = ["0–3", "3–6", "6–10", "10–15", "15–25", "25–50"]


def _base(fig, h=340, margin=None):
    fig.update_layout(height=h, margin=margin or dict(l=10, r=10, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=FONT,
                      hoverlabel=dict(bgcolor=C["navy"], font=dict(color="white", size=12)), showlegend=False)
    return fig


def _axes(fig, x=None, y=None):
    fig.update_xaxes(showgrid=True, gridcolor="#E7E1D5", gridwidth=0.6, zeroline=False, linecolor=C["line"], title=dict(text=x or "", font=dict(size=11, color=C["muted"])), tickfont=dict(size=11, color=C["muted"]))
    fig.update_yaxes(showgrid=True, gridcolor="#E7E1D5", gridwidth=0.6, zeroline=False, linecolor=C["line"], title=dict(text=y or "", font=dict(size=11, color=C["muted"])), tickfont=dict(size=11, color=C["muted"]))
    return fig


def conflict_map(rows, selected=None, h=380):
    fig = go.Figure()
    fig.add_vline(x=0.33, line=dict(color=C["line"], width=1, dash="dot")); fig.add_hline(y=0, line=dict(color=C["line"], width=1, dash="dot"))
    for r in rows:
        sel = r["key"] == selected
        fig.add_trace(go.Scatter(x=[r["delta"]], y=[math.log(r["OR_primary"])], mode="markers+text", text=[SHORT[r["key"]]], textposition="top center", textfont=dict(size=11, color=C["ink"]),
                                 marker=dict(size=max(r["headroom"], 12) * 0.62, color=VERDICT_COLOR.get(r["verdict_display"], C["grey"]), opacity=0.92 if sel or not selected else 0.55,
                                             line=dict(color=C["ink"] if sel else "white", width=2.5 if sel else 1.2)),
                                 hovertemplate=f"<b>{LABEL[r['key']]}</b><br>Internal δ {r['delta']:.2f}<br>Market OR {r['OR_primary']:.2f}<br>Headroom {r['headroom']:.0f}%<br>{r['verdict_display']}<extra></extra>"))
    fig.add_annotation(x=0.78, y=-0.45, text="INTERNAL ↑  MARKET ↓<br><b>CONFLICT</b>", showarrow=False, font=dict(size=10, color=C["red"]), align="right")
    fig.add_annotation(x=0.78, y=0.62, text="BOTH LINES AGREE", showarrow=False, font=dict(size=10, color=C["teal"]), align="right")
    _base(fig, h, dict(l=10, r=10, t=10, b=10)); _axes(fig, "Internal signal — Cliff's δ (JDS)", "Market signal — log odds ratio")
    fig.update_xaxes(range=[0, 0.85]); fig.update_yaxes(range=[-0.55, 0.7])
    return fig


def ek_bars(rows, h=300):
    rs = sorted(rows, key=lambda r: r["Ek"])
    fig = go.Figure(go.Bar(y=[SHORT[r["key"]] for r in rs], x=[r["Ek"] for r in rs], orientation="h", marker_color=[VERDICT_COLOR.get(r["verdict_display"], C["grey"]) for r in rs],
                           error_x=dict(type="data", symmetric=False, array=[r["Ek_hi"] - r["Ek"] for r in rs], arrayminus=[r["Ek"] - r["Ek_lo"] for r in rs], color=C["ink"], thickness=1.2, width=4),
                           hovertemplate="%{y}: %{x:.2f} pp<extra></extra>"))
    _base(fig, h); _axes(fig, "Modelled cohort gain E_k (pp of P(high hike) for a +0.5 step) · 95% bootstrap CI")
    return fig


def effects_forest(effects, h=300):
    es = sorted(effects, key=lambda e: e["delta"])
    fig = go.Figure(go.Scatter(x=[e["delta"] for e in es], y=[SHORT[e["skill"]] for e in es], mode="markers", marker=dict(size=10, color=C["blue"]),
                               error_x=dict(type="data", symmetric=False, array=[e["ci_hi"] - e["delta"] for e in es], arrayminus=[e["delta"] - e["ci_lo"] for e in es], color=C["navy"], thickness=1.3, width=5)))
    fig.add_vline(x=0, line=dict(color=C["grey"], dash="dash", width=1)); _base(fig, h); _axes(fig, "Cliff's δ with 95% bootstrap CI (JDS, n = 139)")
    return fig


def market_forest(market_or, h=320):
    S5, S6 = "S5 +all controls (primary tax.)", "S6 all controls (wide tax. & population)"
    fig = go.Figure(); ks = ["big_data", "coding", "maths_stats", "ai_ml", "story"]
    for spec, col, off, nm in ((S5, C["blue"], 0.14, "Primary taxonomy"), (S6, C["teal"], -0.14, "Wide taxonomy")):
        v = [market_or[spec][k] for k in ks]
        fig.add_trace(go.Scatter(x=[x["OR"] for x in v], y=[i + off for i in range(len(ks))], mode="markers", name=nm, marker=dict(size=9, color=col),
                                 error_x=dict(type="data", symmetric=False, array=[x["hi"] - x["OR"] for x in v], arrayminus=[x["OR"] - x["lo"] for x in v], color=col, thickness=1.2, width=4),
                                 hovertemplate="%{x:.2f}<extra>" + nm + "</extra>"))
    fig.add_vline(x=1, line=dict(color=C["grey"], dash="dash", width=1)); _base(fig, h); _axes(fig, "Odds ratio of a higher salary band (95% CI)")
    fig.update_yaxes(tickmode="array", tickvals=list(range(len(ks))), ticktext=[SHORT[k] for k in ks]); fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.12, x=0))
    return fig


def capability_radar(you, target, h=330):
    ks = ["ai_ml", "coding", "maths_stats", "big_data", "story"]; th = [SHORT[k] for k in ks] + [SHORT[ks[0]]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=[target.get(k, 3) for k in ks] + [target.get(ks[0], 3)], theta=th, name="Target level", line=dict(color=C["teal"], width=1.6, dash="dot"), fill="toself", fillcolor="rgba(47,93,98,.10)"))
    fig.add_trace(go.Scatterpolar(r=[you.get(k, 3) for k in ks] + [you.get(ks[0], 3)], theta=th, name="Your level", line=dict(color=C["blue"], width=2.4), fill="toself", fillcolor="rgba(200,121,65,.12)"))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 5], tickvals=[1, 2, 3, 4, 5], tickfont=dict(size=9, color=C["muted"]), gridcolor="#E7E1D5", linecolor="#E6E2D8"), angularaxis=dict(tickfont=dict(size=11, color=C["ink"]), gridcolor="#E7E1D5"), bgcolor="rgba(0,0,0,0)"),
                      showlegend=True, legend=dict(orientation="h", y=-0.08, x=0.15))
    _base(fig, h, dict(l=30, r=30, t=20, b=30)); fig.update_layout(showlegend=True)
    return fig


def band_chart(values, title="", color=None, h=240, as_pct=True, highlight_top=True):
    vals = [100 * v for v in values] if as_pct else list(values); top = max(range(len(vals)), key=lambda i: vals[i])
    cols = [(color or C["blue"]) if (i == top and highlight_top) else "#B9C7E8" for i in range(len(vals))]
    fig = go.Figure(go.Bar(x=BANDS, y=vals, marker_color=cols, text=[f"{v:.0f}%" for v in vals], textposition="outside", cliponaxis=False, hovertemplate="%{x} LPA: %{y:.1f}%<extra></extra>"))
    _base(fig, h, dict(l=10, r=10, t=20, b=10)); _axes(fig, "Salary band (LPA)", "% " + title); fig.update_yaxes(range=[0, max(vals) * 1.3 + 1], showgrid=False)
    return fig


def dna_radar(you, role, dims, labels, h=420):
    th = [labels[d] for d in dims] + [labels[dims[0]]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=[role[d] for d in dims] + [role[dims[0]]], theta=th, name="ROLE WORK DNA", line=dict(color=C["teal"], width=2.4), fill="toself", fillcolor="rgba(47,93,98,.10)"))
    fig.add_trace(go.Scatterpolar(r=[you[d] for d in dims] + [you[dims[0]]], theta=th, name="YOUR WORK DNA", line=dict(color=C["blue"], width=2.6), fill="toself", fillcolor="rgba(200,121,65,.12)"))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 5], tickvals=[1, 2, 3, 4, 5], tickfont=dict(size=9, color=C["muted"]), gridcolor="#E7E1D5", linecolor="#E6E2D8"),
                                 angularaxis=dict(tickfont=dict(size=11, color=C["ink"]), gridcolor="#E7E1D5"), bgcolor="rgba(0,0,0,0)"), legend=dict(orientation="h", y=-0.06, x=0.12))
    _base(fig, h, dict(l=50, r=50, t=20, b=40)); fig.update_layout(showlegend=True)
    return fig


def model_compare(models: dict, metric="auc", h=300, highlight=None, xlabel="AUC"):
    items = sorted(models.items(), key=lambda kv: kv[1][metric]); names = [k for k, _ in items]
    fig = go.Figure(go.Bar(y=names, x=[v[metric] for _, v in items], orientation="h", marker_color=[C["blue"] if n == highlight else "#B9C7E8" for n in names], text=[f"{v[metric]:.3f}" for _, v in items], textposition="outside", cliponaxis=False))
    _base(fig, h, dict(l=10, r=40, t=10, b=10)); _axes(fig, xlabel); fig.update_xaxes(range=[0, max(v[metric] for _, v in items) * 1.15]); fig.update_yaxes(showgrid=False)
    return fig


def ladder_chart(ladder: dict, h=260):
    ks = list(ladder)
    fig = go.Figure(go.Bar(x=ks, y=[ladder[k]["median_ratio"] for k in ks], marker_color=C["navy3"], error_y=dict(type="data", symmetric=False, array=[ladder[k]["hi"] - ladder[k]["median_ratio"] for k in ks], arrayminus=[ladder[k]["median_ratio"] - ladder[k]["lo"] for k in ks], color=C["ink"], thickness=1.2, width=4),
                           text=[f"{ladder[k]['median_ratio']:.2f}×" for k in ks], textposition="outside", cliponaxis=False))
    _base(fig, h, dict(l=10, r=10, t=20, b=10)); _axes(fig, None, "Senior ÷ junior median pay"); fig.update_yaxes(range=[1, 1.85], showgrid=False)
    return fig
