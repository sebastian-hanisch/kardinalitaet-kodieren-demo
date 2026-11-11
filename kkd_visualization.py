"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import kkd_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_wachstum(xs, formel: dict, gebaut: dict, x_titel: str, titel: str, y_titel: str):
    """Exakte Formel als Linie, gebaute Zahlen als Punkte (logarithmische Achse). `formel[v]` und `gebaut[v]` sind Listen über `xs`;
    Werte 0 (keine Klausel nötig) und nicht gebaute Punkte (None) werden ausgelassen."""
    fig = go.Figure()
    for v in C.VERFAHREN:
        pts = [(x, y) for x, y in zip(xs, formel[v]) if y]
        fig.add_trace(go.Scatter(x=[p[0] for p in pts], y=[p[1] for p in pts], mode="lines", line=dict(color=C.COLOR[v], width=2),
                                 name=f"{C.VERFAHREN_LABEL[v]} (Formel)", hovertemplate="%{x}: %{y:,}<extra>" + C.VERFAHREN_LABEL[v] + " (Formel)</extra>"))
        pts = [(x, y) for x, y in zip(xs, gebaut[v]) if y]
        fig.add_trace(go.Scatter(x=[p[0] for p in pts], y=[p[1] for p in pts], mode="markers", marker=dict(color=C.COLOR[v], size=8, symbol="circle-open-dot"),
                                 name=f"{C.VERFAHREN_LABEL[v]} (gebaut)", hovertemplate="%{x}: %{y:,}<extra>" + C.VERFAHREN_LABEL[v] + " (gebaut)</extra>"))
    fig.update_xaxes(title_text=x_titel)
    fig.update_yaxes(title_text=y_titel, type="log")
    fig.update_layout(title=dict(text=titel, font=dict(size=14)))
    return _base(fig)


def build_streifen(konflikte: dict, budget: int, titel: str):
    """Konflikte je Graph (ein Punkt je Graph) und Kodierung; die Raute ist der Median. Logarithmische Achse; Abbrüche liegen auf dem Budget.
    `konflikte[v]` ist eine Liste (None = nicht gebaut, wird ausgelassen)."""
    fig = go.Figure()
    sichtbar = [(v, w) for v, w in konflikte.items() if not any(x is None for x in w)]
    for pos, (v, werte) in enumerate(sichtbar):
        label = C.VERFAHREN_LABEL[v]
        n = len(werte)
        xs = [pos + (i / max(n - 1, 1) - 0.5) * 0.5 for i in range(n)]       # fester Versatz je Graph: dieselbe Reihenfolge in jeder Kodierung
        fig.add_trace(go.Scatter(x=xs, y=[max(w, 0.5) for w in werte], mode="markers", marker=dict(color=C.COLOR[v], size=9, opacity=0.65),
                                 name=label, customdata=[[i + 1, w] for i, w in enumerate(werte)],
                                 hovertemplate="Graph %{customdata[0]}: %{customdata[1]:,} Konflikte<extra>" + label + "</extra>"))
        ordnung = sorted(werte)
        med = ordnung[n // 2] if n % 2 else (ordnung[n // 2 - 1] + ordnung[n // 2]) / 2
        fig.add_trace(go.Scatter(x=[pos], y=[max(med, 0.5)], mode="markers", marker=dict(color="rgba(0,0,0,0)", size=17, symbol="diamond-open",
                                 line=dict(color=C.COLOR[v], width=3)), showlegend=False, hovertemplate=f"Median {med:,.1f}<extra>{label}</extra>"))
    fig.update_xaxes(tickvals=list(range(len(sichtbar))), ticktext=[C.VERFAHREN_LABEL[v] for v, _ in sichtbar], range=[-0.6, max(len(sichtbar) - 1, 0) + 0.6])
    fig.update_yaxes(title_text="Konflikte je Graph (logarithmisch; Raute = Median)", type="log")
    fig.update_layout(title=dict(text=titel, font=dict(size=14)), showlegend=False)
    if any(max(w) >= budget for _, w in sichtbar):
        fig.add_hline(y=budget, line_dash="dot", line_color="rgba(150,150,150,0.8)", annotation_text="Budget", annotation_position="top left")
    return _base(fig)
