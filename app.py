"""OAU campus transport study: report and interactive dashboard (Streamlit).

Run locally with ``streamlit run app.py``. Every data file sits next to this
file; team credits come from ``team.csv`` (edit it to change names/roles).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import cng_data as D

HERE = Path(__file__).resolve().parent

st.set_page_config(
    page_title="OAU Campus Transport Study",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================================================
# Design system
# ==========================================================================
INK = "#1d2a2e"
MUTED = "#5b6b70"
TEAL = "#1f6f78"
AMBER = "#d99a00"
RED = "#c8553d"
PAPER = "#fbfaf7"
TYPE_COLORS = {"CNG bus": TEAL, "Keke": AMBER}
BLOCK_COLORS = {"AM": "#3b7dd8", "MD": "#8a63d2", "PM": RED}
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
FONT = "Inter, -apple-system, Segoe UI, sans-serif"

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap');
html, body, [class*="css"], .stMarkdown, p, li, label, input, textarea, button {{
    font-family: {FONT};
}}
.block-container {{ padding-top: 4.2rem; padding-bottom: 1rem; max-width: 1240px; }}
h1, h2, h3, .serif {{ font-family: 'Source Serif 4', Georgia, serif !important; color: {INK}; letter-spacing: -0.01em; }}
h1 {{ font-weight: 700 !important; }}
h2 {{ font-weight: 600 !important; margin-top: 2.4rem !important; padding-top: .6rem;
      border-top: 1px solid rgba(0,0,0,.08); }}
h3 {{ font-weight: 600 !important; margin-top: 1.4rem !important; }}
.article p, .article li {{ font-size: 1.04rem; line-height: 1.7; color: #26363b; }}
.kicker {{ text-transform: uppercase; letter-spacing: .14em; font-size: .78rem; font-weight: 600; color: {TEAL}; }}
.dek {{ font-family: 'Source Serif 4', Georgia, serif; font-size: 1.28rem; line-height: 1.55; color: #34474d; max-width: 60rem; }}
.byline {{ color: {MUTED}; font-size: .92rem; margin: .6rem 0 1.4rem; }}
div[data-testid="stMetric"] {{
    background: white; border: 1px solid rgba(31,111,120,.16); border-radius: 12px;
    padding: 12px 16px; box-shadow: 0 1px 2px rgba(0,0,0,.03);
}}
div[data-testid="stMetricLabel"] p {{ font-size: .82rem; color: {MUTED}; }}
div[data-testid="stMetricValue"] {{ font-family: 'Source Serif 4', Georgia, serif; color: {INK}; font-size: 1.85rem; }}
.explain {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0; margin: -.4rem 0 1.6rem;
    border: 1px solid rgba(31,111,120,.18); border-radius: 12px; overflow: hidden; background: white; }}
.explain > div {{ padding: .85rem 1.05rem; font-size: .93rem; line-height: 1.55; color: #2c3c41; }}
.explain > div:first-child {{ background: rgba(31,111,120,.05); border-right: 1px solid rgba(31,111,120,.14); }}
.explain b.lbl {{ display: block; font-size: .72rem; letter-spacing: .12em; text-transform: uppercase; color: {TEAL}; margin-bottom: .25rem; }}
@media (max-width: 760px) {{ .explain {{ grid-template-columns: 1fr; }}
    .explain > div:first-child {{ border-right: none; border-bottom: 1px solid rgba(31,111,120,.14); }} }}
.callout {{ border-left: 4px solid {TEAL}; background: rgba(31,111,120,.06); padding: .9rem 1.1rem;
    border-radius: 0 10px 10px 0; margin: 1rem 0 1.4rem; font-size: 1rem; line-height: 1.6; }}
.callout.warn {{ border-left-color: {AMBER}; background: rgba(217,154,0,.08); }}
.pipeline {{ display: flex; flex-wrap: wrap; gap: .5rem; align-items: stretch; margin: .6rem 0 1.4rem; }}
.pipeline .step {{ flex: 1 1 150px; background: white; border: 1px solid rgba(0,0,0,.08); border-radius: 12px; padding: .75rem .9rem; }}
.pipeline .step b {{ display:block; color: {TEAL}; font-size: .78rem; letter-spacing: .1em; text-transform: uppercase; margin-bottom: .2rem; }}
.pipeline .step span {{ font-size: .9rem; color: #33444a; line-height: 1.45; }}
.pipeline .arrow {{ align-self: center; color: {MUTED}; font-size: 1.3rem; }}
.sheet-card {{ background: white; border: 1px solid rgba(0,0,0,.08); border-radius: 12px; padding: 1rem 1.1rem; height: 100%; }}
.sheet-card h4 {{ margin: 0 0 .35rem; font-family: 'Source Serif 4', Georgia, serif; font-size: 1.08rem; color: {INK}; }}
.sheet-card .meta {{ font-size: .8rem; color: {TEAL}; font-weight: 600; margin-bottom: .4rem; }}
.sheet-card p {{ font-size: .92rem; line-height: 1.55; margin: 0; color: #33444a; }}
.team-card {{ background: white; border: 1px solid rgba(0,0,0,.08); border-radius: 14px; padding: 1rem 1.1rem; margin-bottom: .9rem; min-height: 150px; }}
.team-card .avatar {{ width: 42px; height: 42px; border-radius: 50%; background: {TEAL}; color: white;
    display: inline-flex; align-items: center; justify-content: center; font-weight: 700; margin-bottom: .5rem; }}
.team-card .nm {{ font-family: 'Source Serif 4', Georgia, serif; font-weight: 600; font-size: 1.1rem; color: {INK}; }}
.team-card .rl {{ font-size: .8rem; color: {TEAL}; font-weight: 600; margin-bottom: .35rem; }}
.team-card .ct {{ font-size: .9rem; color: #33444a; line-height: 1.5; }}
.site-footer {{ margin-top: 3rem; padding: 1.4rem 0 .4rem; border-top: 1px solid rgba(0,0,0,.1); color: {MUTED}; font-size: .86rem; line-height: 1.6; }}
.site-footer b {{ color: {INK}; }}
table.metrics {{ width: 100%; border-collapse: collapse; font-size: .93rem; margin: .4rem 0 1.4rem; }}
table.metrics th {{ text-align: left; font-size: .75rem; letter-spacing: .1em; text-transform: uppercase; color: {TEAL}; border-bottom: 2px solid rgba(31,111,120,.3); padding: .5rem .6rem; }}
table.metrics td {{ border-bottom: 1px solid rgba(0,0,0,.07); padding: .6rem; vertical-align: top; line-height: 1.5; color: #2c3c41; }}
table.metrics td:first-child {{ font-weight: 600; color: {INK}; white-space: nowrap; }}
</style>
""",
    unsafe_allow_html=True,
)


def style(fig: go.Figure, height: int = 420, title: str | None = None,
          subtitle: str | None = None) -> go.Figure:
    text = f"<b>{title}</b>" if title else None
    if title and subtitle:
        text += f"<br><span style='font-size:13px;color:{MUTED}'>{subtitle}</span>"
    fig.update_layout(
        template="plotly_white",
        height=height,
        font=dict(family=FONT, size=13, color=INK),
        margin=dict(l=10, r=20, t=100 if subtitle else 80, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0, title_text=""),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(font_family=FONT),
    )
    if text:
        fig.update_layout(title=dict(text=text, x=0, y=0.97, yanchor="top", yref="container",
                                     font=dict(size=17, family="Source Serif 4, Georgia, serif")))
    fig.update_xaxes(gridcolor="rgba(0,0,0,.06)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(0,0,0,.06)", zeroline=False)
    return fig


def show(fig: go.Figure) -> None:
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False})


def explain(how: str, what: str) -> None:
    """Plain-language 'how to read' / 'what it shows' panel under a chart."""
    st.markdown(
        f"<div class='explain'><div><b class='lbl'>How to read this chart</b>{how}</div>"
        f"<div><b class='lbl'>What it shows</b>{what}</div></div>",
        unsafe_allow_html=True,
    )


def callout(text: str, warn: bool = False) -> None:
    st.markdown(f"<div class='callout{' warn' if warn else ''}'>{text}</div>", unsafe_allow_html=True)


def md(text: str) -> None:
    st.markdown(f"<div class='article'>\n\n{text}\n\n</div>", unsafe_allow_html=True)


def hh(h: float) -> str:
    return f"{int(h):02d}:00" if pd.notna(h) else "—"


# ==========================================================================
# Data
# ==========================================================================
@st.cache_data(show_spinner="Loading field observations…")
def frames() -> dict[str, pd.DataFrame]:
    return D.load_frames()


@st.cache_data
def table(name: str) -> pd.DataFrame:
    path = HERE / name
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


@st.cache_data
def team() -> pd.DataFrame:
    path = HERE / "team.csv"
    if not path.exists():
        return pd.DataFrame(columns=["name", "role", "contributions"])
    return pd.read_csv(path).fillna("")


F = frames()
Q_ALL = F["queue"][F["queue"]["valid_route"]]
W_ALL = F["wait"][F["wait"]["valid_route"]]
V_ALL = F["vehicle"][F["vehicle"]["valid_route"]]
SURVEY = table("survey_clean.csv")
TESTS = table("hypothesis_tests.csv")
SPEARMAN = table("spearman_correlations.csv")
COMPARE = table("survey_observed_wait_comparison.csv")
TEAM = team()


def completed(w: pd.DataFrame) -> pd.DataFrame:
    return w.loc[w["wait_event"]]


def vehicle_metrics(v: pd.DataFrame) -> pd.DataFrame:
    v = v.copy()
    v["cap"] = pd.to_numeric(v["Capacity"], errors="coerce").fillna(v["Type"].map(D.CAPACITIES))
    v["boarded_n"] = pd.to_numeric(v["Boarded"], errors="coerce")
    v["left_n"] = pd.to_numeric(v["Left behind"], errors="coerce")
    v["load"] = v["boarded_n"] / v["cap"]
    return v


# ==========================================================================
# Chart builders (shared by the report and the dashboard)
# ==========================================================================
def fig_wait_hist(c: pd.DataFrame) -> go.Figure:
    fig = px.histogram(c, x="wait_minutes", color="Type used", nbins=45, barmode="overlay",
                       opacity=0.72, color_discrete_map=TYPE_COLORS,
                       labels={"wait_minutes": "minutes waited", "Type used": "Type"})
    fig.update_yaxes(title="number of passengers")
    return style(fig, 400, "How long did people wait?", "Completed waits, by vehicle type boarded")


def fig_ecdf(c: pd.DataFrame) -> go.Figure:
    fig = px.ecdf(c, x="wait_minutes", color="Type used", color_discrete_map=TYPE_COLORS,
                  labels={"wait_minutes": "minutes waited", "Type used": "Type"})
    for t in (5, 10, 15):
        fig.add_vline(x=t, line_dash="dot", line_color="#999",
                      annotation_text=f"{t} min", annotation_position="bottom right")
    fig.update_yaxes(title="share already boarded", tickformat=".0%")
    return style(fig, 400, "Share of passengers boarded by each minute",
                 "Read up from a minute mark to see what share had boarded by then")


def fig_wait_by_route(c: pd.DataFrame) -> go.Figure:
    g = (c.groupby("stop_direction")["wait_minutes"]
         .agg(mean="mean", median="median", p90=lambda s: s.quantile(.9), n="count")
         .reset_index().sort_values("mean"))
    fig = go.Figure()
    fig.add_bar(y=g["stop_direction"], x=g["mean"], orientation="h", name="Average wait",
                marker_color=TEAL, customdata=g[["median", "p90", "n"]],
                hovertemplate="%{y}<br>Average %{x:.1f} min · typical (median) %{customdata[0]:.0f} min"
                              "<br>1-in-10 worst: %{customdata[1]:.0f}+ min<br>%{customdata[2]:,} passengers<extra></extra>")
    fig.add_scatter(y=g["stop_direction"], x=g["p90"], mode="markers", name="Worst 10% wait at least…",
                    marker=dict(symbol="line-ns-open", size=18, color=RED, line_width=3))
    fig.update_xaxes(title="minutes")
    return style(fig, 470, "Average wait at each stop and direction",
                 "Bars = average; red tick = the wait the unluckiest 1 in 10 passengers faced")


def fig_boarding(c: pd.DataFrame, thr: int = 10) -> go.Figure:
    rows = []
    for route, grp in c.groupby("stop_direction"):
        n = len(grp)
        k = int(grp["wait_minutes"].le(thr).sum())
        lo, hi = D.wilson_interval(k, n)
        rows.append({"route": route, "share": k / n, "lo": lo, "hi": hi, "n": n})
    bp = pd.DataFrame(rows).sort_values("share")
    fig = go.Figure(go.Bar(
        y=bp["route"], x=bp["share"], orientation="h",
        marker=dict(color=bp["share"], colorscale=[[0, RED], [0.5, AMBER], [1, TEAL]], cmin=0.4, cmax=1),
        error_x=dict(type="data", symmetric=False, array=bp["hi"] - bp["share"],
                     arrayminus=bp["share"] - bp["lo"], color="#555", thickness=1.4),
        text=bp["share"].map("{:.0%}".format), textposition="inside",
        customdata=bp[["n", "lo", "hi"]],
        hovertemplate="%{y}<br>%{x:.1%} boarded within " + str(thr) +
                      " min<br>95% range %{customdata[1]:.0%}–%{customdata[2]:.0%} · n=%{customdata[0]:,}<extra></extra>",
    ))
    fig.update_xaxes(tickformat=".0%", range=[0, 1.03], title=f"share of passengers boarded within {thr} minutes")
    return style(fig, 470, f"Chance of boarding within {thr} minutes",
                 "Black whiskers show the 95% confidence range")


def fig_block_box(c: pd.DataFrame) -> go.Figure:
    fig = px.box(c, x="Block", y="wait_minutes", color="Block", points=False,
                 category_orders={"Block": ["AM", "MD", "PM"]}, color_discrete_map=BLOCK_COLORS,
                 labels={"wait_minutes": "minutes waited", "Block": ""})
    fig.update_xaxes(ticktext=["Morning (before 11:00)", "Midday (11:00–15:00)", "Evening (after 15:00)"],
                     tickvals=["AM", "MD", "PM"])
    fig.update_layout(showlegend=False)
    return style(fig, 400, "Waits by time of day")


def fig_wait_by_hour(c: pd.DataFrame) -> go.Figure:
    hr = c.groupby(["hour_slot", "Type used"])["wait_minutes"].median().reset_index()
    fig = px.line(hr, x="hour_slot", y="wait_minutes", color="Type used", markers=True,
                  color_discrete_map=TYPE_COLORS,
                  labels={"hour_slot": "hour the passenger joined the queue",
                          "wait_minutes": "typical (median) wait, min", "Type used": "Type"})
    fig.update_xaxes(dtick=1)
    return style(fig, 400, "Typical wait by hour of arrival")


def fig_queue_rhythm(q: pd.DataFrame) -> go.Figure:
    g = q.groupby("hour_slot").agg(mean_queue=("Queue size", "mean"),
                                   arrivals=("New arrivals (10 min)", "mean")).reset_index()
    fig = go.Figure()
    fig.add_bar(x=g["hour_slot"], y=g["arrivals"] * 6, name="New passengers arriving per hour (avg per stop)",
                marker_color="rgba(217,154,0,.55)")
    fig.add_scatter(x=g["hour_slot"], y=g["mean_queue"], name="People standing in the queue (avg, right axis)",
                    mode="lines+markers", line=dict(color=TEAL, width=3), yaxis="y2")
    fig.update_layout(yaxis2=dict(title="people in queue", overlaying="y", side="right", rangemode="tozero",
                                  showgrid=False, color=TEAL))
    fig.update_xaxes(title="hour of day", dtick=1)
    fig.update_layout(yaxis=dict(title="new passengers per hour", rangemode="tozero"))
    fig.update_layout(yaxis2=dict(tickformat=".0f"))
    return style(fig, 430, "The daily rhythm", "Demand (bars, left axis) and queue length (line, right axis) through the day")


def queue_by_route_hour(q: pd.DataFrame) -> pd.DataFrame:
    return (q.groupby(["stop_direction", "hour_slot"])
            .agg(mean_queue=("Queue size", "mean"), max_queue=("Queue size", "max"),
                 n=("Queue size", "count")).reset_index())


def fig_queue_heat(q: pd.DataFrame) -> go.Figure:
    per = queue_by_route_hour(q)
    order = per.groupby("stop_direction")["mean_queue"].max().sort_values(ascending=False).index
    heat = per.pivot(index="stop_direction", columns="hour_slot", values="mean_queue").loc[order]
    fig = px.imshow(heat, aspect="auto", color_continuous_scale="YlOrRd", text_auto=".0f",
                    labels=dict(x="hour of day", y="", color="avg queue"))
    fig.update_xaxes(dtick=1)
    return style(fig, 480, "Where and when queues build", "Average number of people waiting, by stop-direction and hour")


def fig_rush(q: pd.DataFrame, routes: list[str]) -> go.Figure:
    per = queue_by_route_hour(q)
    fig = px.line(per[per["stop_direction"].isin(routes)], x="hour_slot", y="mean_queue",
                  color="stop_direction", markers=True,
                  labels={"hour_slot": "hour of day", "mean_queue": "average queue (people)", "stop_direction": ""})
    fig.update_xaxes(dtick=1)
    return style(fig, 420, "Rush-hour profile of the busiest routes")


def fig_weekday_weekend(q: pd.DataFrame) -> go.Figure:
    hourly = (q.groupby(["Date", "is_weekend", "stop_direction", "hour_slot"])["New arrivals (10 min)"]
              .mean().mul(6).reset_index(name="arr"))
    hourly["Day type"] = np.where(hourly["is_weekend"], "Weekend", "Weekday")
    agg = hourly.groupby(["Day type", "hour_slot"])["arr"].mean().reset_index()
    fig = px.line(agg, x="hour_slot", y="arr", color="Day type", markers=True,
                  color_discrete_map={"Weekday": TEAL, "Weekend": AMBER},
                  labels={"hour_slot": "hour of day", "arr": "passengers arriving per hour (per route)"})
    fig.update_xaxes(dtick=1)
    return style(fig, 400, "Weekday vs weekend demand")


def fig_friday(q: pd.DataFrame) -> go.Figure:
    sub = q[q["Stop"].isin(["NEW MARKET", "HALL"]) & q["hour"].between(13, 14.5)
            & ~q["is_weekend"]].copy()
    sub["Day group"] = np.where(sub["Day"].eq("Friday"), "Friday", "Mon–Thu")
    g = sub.groupby(["Stop", "Day group"])["Queue size"].mean().reset_index()
    fig = px.bar(g, x="Stop", y="Queue size", color="Day group", barmode="group", text_auto=".1f",
                 color_discrete_map={"Friday": RED, "Mon–Thu": "#9fb4b8"},
                 labels={"Queue size": "average queue, 13:00–14:30", "Stop": ""})
    return style(fig, 380, "The Friday early-afternoon surge")


def fig_vehicle_day(v: pd.DataFrame, q: pd.DataFrame, date, route: str) -> go.Figure:
    vv = vehicle_metrics(v[(v["Date"].dt.date == date) & (v["stop_direction"] == route)])
    vv = vv.dropna(subset=["Arrived minutes"]).sort_values("Arrived minutes")
    t = pd.to_datetime(vv["Arrived minutes"], unit="m", origin=pd.Timestamp(date))
    fig = go.Figure()
    for typ, color in TYPE_COLORS.items():
        m = vv["Type"].eq(typ)
        fig.add_bar(x=t[m], y=vv.loc[m, "boarded_n"], name=f"{typ}: boarded", marker_color=color,
                    customdata=vv.loc[m, ["Vehicle ID", "Arrived", "Departed", "cap"]],
                    hovertemplate="%{customdata[0]} arrived %{customdata[1]}, left %{customdata[2]}"
                                  "<br>boarded %{y} of %{customdata[3]:.0f} seats<extra></extra>")
    fig.add_bar(x=t, y=-vv["left_n"], name="left behind at the kerb", marker_color="rgba(200,85,61,.55)",
                hovertemplate="%{customdata} left behind<extra></extra>", customdata=vv["left_n"])
    qq = q[(q["Date"].dt.date == date) & (q["stop_direction"] == route)].sort_values("Time minutes")
    if len(qq):
        fig.add_scatter(x=pd.to_datetime(qq["Time minutes"], unit="m", origin=pd.Timestamp(date)),
                        y=qq["Queue size"], name="queue count (every 10 min)", mode="lines",
                        line=dict(color=INK, width=2, dash="dot"))
    fig.update_layout(barmode="relative", bargap=0.05)
    fig.update_xaxes(title="time of day", tickformat="%H:%M")
    fig.update_yaxes(title="people  (↑ boarded · ↓ left behind)")
    return style(fig, 460, f"A day of vehicle arrivals: {route.replace(' -> ', ' → ')}",
                 f"{pd.Timestamp(date):%A %d %B %Y} · each bar is one vehicle pulling in")


def fig_load(load: pd.DataFrame) -> go.Figure:
    fig = px.bar(load.sort_values("load_factor_pct"), y="stop_direction", x="load_factor_pct", color="Type",
                 barmode="group", orientation="h", color_discrete_map=TYPE_COLORS,
                 labels={"load_factor_pct": "average % of seats filled when leaving", "stop_direction": ""})
    fig.add_vline(x=100, line_dash="dot", line_color=RED, annotation_text="full", annotation_position="top")
    return style(fig, 480, "How full are vehicles when they leave?")


def fig_left_behind(load: pd.DataFrame) -> go.Figure:
    fig = px.bar(load.sort_values("left_behind_rate"), y="stop_direction", x="left_behind_rate", color="Type",
                 barmode="group", orientation="h", color_discrete_map=TYPE_COLORS,
                 labels={"left_behind_rate": "left behind ÷ (boarded + left behind)", "stop_direction": ""})
    fig.update_xaxes(tickformat=".0%")
    return style(fig, 480, "How often are people left behind?")


def fig_headway(headway: pd.DataFrame) -> go.Figure:
    hw = headway.dropna(subset=["median_headway_min"])
    heat = hw.pivot(index="stop_direction", columns="hour_slot", values="median_headway_min")
    fig = px.imshow(heat, aspect="auto", color_continuous_scale="Blues", text_auto=".0f",
                    labels=dict(x="hour of day", y="", color="minutes"))
    fig.update_xaxes(dtick=1)
    return style(fig, 440, "Minutes between vehicles (headway)", "Typical gap between one vehicle and the next")


def fig_dc(dc: pd.DataFrame) -> go.Figure:
    dc = dc.dropna(subset=["demand_to_capacity_ratio"])
    heat = dc.pivot(index="stop_direction", columns="hour_slot", values="demand_to_capacity_ratio")
    fig = px.imshow(heat, aspect="auto", color_continuous_scale="RdYlGn_r", zmin=0, zmax=2, text_auto=".1f",
                    labels=dict(x="hour of day", y="", color="ratio"))
    fig.update_xaxes(dtick=1)
    return style(fig, 460, "Passengers arriving ÷ seats leaving", "Above 1.0 (red) = more people turn up than there are seats")


def fig_effects(t: pd.DataFrame) -> go.Figure:
    t = t.dropna(subset=["effect_size"]).copy()
    t["label"] = t["question"] + " · " + t["test_name"]
    t = t.iloc[::-1]
    sig = t["p_value"].lt(0.05)
    fig = go.Figure(go.Scatter(
        x=t["effect_size"], y=t["label"], mode="markers",
        marker=dict(size=13, color=np.where(sig, TEAL, "#aaaaaa")),
        error_x=dict(type="data", symmetric=False,
                     array=(t["effect_size_ci95_high"] - t["effect_size"]).fillna(0),
                     arrayminus=(t["effect_size"] - t["effect_size_ci95_low"]).fillna(0)),
        customdata=t[["effect_size_name", "p_value"]],
        hovertemplate="%{y}<br>%{customdata[0]} = %{x:.2f} · p = %{customdata[1]:.2g}<extra></extra>",
    ))
    fig.add_vline(x=0, line_color="#999")
    for x, lab in ((0.1, "small"), (0.3, "medium"), (0.5, "large")):
        fig.add_vline(x=x, line_dash="dot", line_color="#ddd", annotation_text=lab, annotation_position="top")
    fig.update_xaxes(title="effect size (0 = no difference, ±1 = complete separation)", range=[-0.45, 1])
    return style(fig, 470, "How big is each difference?", "Dots = effect size; bars = 95% confidence range")


def fig_spearman(sp: pd.DataFrame) -> go.Figure:
    names = {"queue": "queue size", "arrivals": "arrivals", "wait": "waiting time", "hour_slot": "hour of day",
             "load_factor": "how full vehicles leave", "headway": "gap between vehicles"}
    sp = sp.set_index("variable").rename(index=names, columns=names)
    sp.index.name = None
    fig = px.imshow(sp, text_auto=".2f", color_continuous_scale="RdBu_r",
                    zmin=-1, zmax=1, aspect="auto")
    return style(fig, 430, "Which measures move together?", "Spearman correlation: +1 rise together, −1 opposite, 0 unrelated")


def fig_perceived(comp: pd.DataFrame) -> go.Figure:
    comp = comp.dropna(subset=["observed_wait_mean_min"])
    fig = go.Figure()
    fig.add_bar(x=comp["boarding_stop"], y=comp["reported_wait_mean_min"], name="What students said (survey)",
                marker_color=AMBER, customdata=comp["reported_wait_n"],
                hovertemplate="%{x}: %{y:.1f} min (%{customdata} students)<extra></extra>")
    fig.add_bar(x=comp["boarding_stop"], y=comp["observed_wait_mean_min"], name="What we timed (field)",
                marker_color=TEAL, customdata=comp["observed_wait_n"],
                hovertemplate="%{x}: %{y:.1f} min (%{customdata:,} timed waits)<extra></extra>")
    fig.update_yaxes(title="average wait (min)")
    return style(fig, 400, "Perceived vs measured waiting time")


def fig_survey_bar(s: pd.DataFrame, col: str, title: str, order: list[str] | None = None) -> go.Figure:
    vc = s[col].value_counts()
    if order:
        vc = vc.reindex(order).dropna()
    df = vc.reset_index()
    df.columns = ["answer", "count"]
    df["share"] = df["count"] / df["count"].sum()
    fig = px.bar(df, x="count", y="answer", orientation="h", text=df["share"].map("{:.0%}".format),
                 color_discrete_sequence=[TEAL], labels={"answer": "", "count": "students"})
    fig.update_yaxes(categoryorder="array", categoryarray=list(df["answer"])[::-1])
    return style(fig, 330, title)


def fig_multi(s: pd.DataFrame, col: str, title: str) -> go.Figure:
    ex = s[col].dropna().str.split(r",\s*").explode().str.strip()
    vc = ex[ex.ne("")].value_counts().head(8).reset_index()
    vc.columns = ["option", "count"]
    vc["share"] = vc["count"] / len(s)
    fig = px.bar(vc.iloc[::-1], x="count", y="option", orientation="h", text=vc["share"].iloc[::-1].map("{:.0%}".format),
                 color_discrete_sequence=[AMBER], labels={"option": "", "count": "students choosing it"})
    fig.update_yaxes(dtick=1, automargin=True)
    return style(fig, 360, title, "Students could pick more than one")


SURVEY_ORDERS = {
    "typical_wait": ["0 to 5 minutes", "6 to 10 minutes", "11 to 15 minutes", "16 to 30 minutes", "More than 30 minutes"],
    "longest_wait": ["0 to 5 minutes", "6 to 15 minutes", "16 to 30 minutes", "31 to 60 minutes", "More than 60 minutes"],
    "failed_boarding": ["Never", "Rarely", "Sometimes", "Often", "Always"],
    "walking_time": ["Less than 1 minute", "1 to 5 minutes", "6 to 10 minutes", "More than 10 minutes"],
    "fare_affordability": ["Very affordable", "Somewhat affordable", "Neither affordable nor expensive",
                           "Somewhat expensive", "Very expensive"],
    "safety": ["Very unsafe", "Unsafe", "Neutral", "Safe", "Very safe"],
    "comfort": ["Very uncomfortable", "Uncomfortable", "Neutral", "Comfortable", "Very comfortable"],
    "usage_frequency": ["Daily", "Several times a week", "Once a week", "Occasionally"],
}
SURVEY_Q = {
    "typical_wait": "Typical wait before boarding", "longest_wait": "Longest wait ever experienced",
    "failed_boarding": "How often the first vehicle is too full to board", "walking_time": "Walk to the nearest stop",
    "fare_affordability": "Fare affordability", "safety": "How safe they feel", "comfort": "Comfort",
    "tracking_app": "Would use a vehicle-tracking app", "transport_used": "Transport type used",
    "transport_preference": "Preferred transport type", "usage_frequency": "How often they ride",
    "boarding_stop": "Usual boarding stop", "destination": "Usual destination",
    "travel_purpose": "Main reason for travelling", "directness": "Does it go directly to their destination?",
}

# Plain-language explanations reused on the report and dashboard
HOW = {
    "hist": "Each bar counts how many timed passengers waited that many minutes. Teal = CNG bus riders, amber = Keke riders; where they overlap the colour is darker. A tall bar on the left means many people boarded almost immediately.",
    "ecdf": "Pick a minute on the bottom axis (the dotted lines mark 5, 10 and 15) and read the height of each line: that is the share of passengers who had already boarded by then. The higher and further left a line is, the better the service.",
    "route": "Each row is one stop and the direction of travel (e.g. <i>NEW MARKET → ACADEMICS</i> means people waiting at New Market to go to the academic area). The bar is the average wait; the red tick shows the wait that the unluckiest 10% of passengers met or exceeded.",
    "boarding": "Each bar is the percentage of passengers at that stop-direction who boarded within the threshold. The thin black whisker is the 95% confidence range: the true value is very likely inside it. Short whiskers mean lots of data.",
    "box": "The box covers the middle half of all waits; the line inside is the typical (median) wait; the whiskers stretch to the usual range. Higher boxes mean longer waits.",
    "hour": "Each point is the typical (median) wait for people who joined the queue during that hour, split by the vehicle type they eventually boarded.",
    "rhythm": "The amber bars (left axis) show how many new passengers arrive at an average stop-direction each hour. The teal line (right axis) shows how many people are standing in the queue at that time. When arrivals rise faster than vehicles take people away, the line climbs.",
    "heat": "Rows are stop-directions, columns are hours of the day. Each square shows the average queue size; darker red = longer queue. Read across a row to see a stop's rush hour; read down a column to compare stops at the same time.",
    "rush": "Each line is one stop-direction. The higher the line at a given hour, the more people were queuing then.",
    "wkend": "Each line shows how many passengers, on average, turned up at a route in each hour. Teal = Monday–Friday, amber = Saturday–Sunday.",
    "friday": "Bars compare the average queue between 13:00 and 14:30 on Fridays (red) with the same window on Monday–Thursday (grey), at New Market and Hall.",
    "vday": "Every coloured bar pointing <b>up</b> is one vehicle arriving: its height is how many people boarded (teal CNG bus, amber Keke). The red bar pointing <b>down</b> underneath is how many people it left behind because it was full. The dotted line is the queue count taken every 10 minutes. Hover a bar to see the vehicle ID and its arrival and departure times.",
    "load": "The bar shows how full vehicles were, on average, when they pulled away: 100% (dotted line) means every seat was taken. Teal = CNG bus (13 seats), amber = Keke (5 seats).",
    "left": "For every vehicle that left, we added the people who boarded and the people left standing. This bar is the left-behind share of that total. A person who misses two vehicles is counted twice, so read it as 'how often vehicles leave people behind', not 'how many different people'.",
    "headway": "Each square is the typical number of minutes between one vehicle arriving and the next, for that stop-direction and hour. Pale = vehicles come often; dark blue = long gaps.",
    "dc": "We divided the passengers arriving in an hour by the seats on vehicles departing in that hour. Green (below 1) = enough seats; red (above 1) = more people than seats, so the queue must grow.",
    "effects": "Each dot is one statistical comparison. The further the dot is from the zero line, the bigger the difference between the two groups. The bar is the 95% confidence range. Teal = statistically significant (p < 0.05); grey = not.",
    "spearman": "Each square shows how strongly two measures rise and fall together across stop-hours. Dark red near +1 = they rise together; dark blue near −1 = one rises as the other falls; white near 0 = no link.",
    "perceived": "For each stop, the amber bar is the average wait students <i>said</i> they usually have (survey), and the teal bar is the average wait we actually <i>timed</i> there.",
    "survey": "Each bar shows how many surveyed students gave that answer; the label is the share of all respondents.",
}


# ==========================================================================
# Footer (every page)
# ==========================================================================
def footer() -> None:
    names = " · ".join(TEAM["name"].tolist()) if len(TEAM) else "the project team"
    st.markdown(
        f"""<div class='site-footer'>
        <b>OAU Campus Transport Study</b>: field observation of CNG bus and Keke services at Obafemi Awolowo University, Ile-Ife.<br>
        <b>Built and researched by:</b> {names}.<br>
        Field data collected 26 October – 1 November 2026 (plus earlier sessions in late September); student survey October–November 2026.
        Analysis in Python (pandas, SciPy); dashboard built with Streamlit and Plotly.
        </div>""",
        unsafe_allow_html=True,
    )


# ==========================================================================
# PAGE 1: REPORT (article)
# ==========================================================================
def page_report() -> None:
    c_all = completed(W_ALL)
    vm = vehicle_metrics(V_ALL)
    headway, load, dc = D.vehicle_efficiency(Q_ALL, V_ALL)
    load = load.dropna(subset=["Type"])
    within10 = c_all["wait_minutes"].le(10).mean()
    left_share = vm["left_n"].sum() / (vm["boarded_n"].sum() + vm["left_n"].sum())
    by_type = c_all.groupby("Type used")["wait_minutes"]
    by_block = c_all.groupby("Block")["wait_minutes"]
    within_block = c_all.assign(ok=c_all["wait_minutes"].le(10)).groupby("Block")["ok"].mean()
    rb = c_all.groupby(["stop_direction", "Block"])["wait_minutes"].agg(["mean", "median", "count"])
    worst = rb[rb["count"] >= 30]["mean"].idxmax()
    worst_row = rb.loc[worst]
    route_ok = c_all.assign(ok=c_all["wait_minutes"].le(10)).groupby("stop_direction")["ok"].agg(["mean", "count"])
    per = queue_by_route_hour(Q_ALL)
    peak = per.loc[per["mean_queue"].idxmax()]
    daily = Q_ALL.groupby(["Date", "is_weekend"])["New arrivals (10 min)"].sum().groupby(level=1).mean()
    over = dc[dc["demand_to_capacity_ratio"] > 1].sort_values("demand_to_capacity_ratio", ascending=False)
    n_obs = len(Q_ALL) + len(W_ALL) + len(V_ALL)

    # ---- Masthead -------------------------------------------------------
    st.markdown("<div class='kicker'>Field study · Campus mobility · OAU Ile-Ife</div>", unsafe_allow_html=True)
    st.markdown("# Waiting for a ride: queues, waits and seats on OAU campus transport")
    st.markdown(
        "<div class='dek'>For one week we went in pairs to five of the busiest campus stops and stood there from 8 a.m. to 6 p.m., "
        "timing passengers, counting queues and logging every CNG bus and Keke that pulled in. "
        "This is what we did, why we measured what we measured, and what we found.</div>",
        unsafe_allow_html=True,
    )
    names = ", ".join(TEAM["name"].tolist())
    st.markdown(f"<div class='byline'>By {names} · November 2026 · {n_obs:,} field records and {len(SURVEY)} survey responses</div>",
                unsafe_allow_html=True)

    k = st.columns(5)
    k[0].metric("Typical wait", f"{c_all['wait_minutes'].median():.0f} min", help="Median of all completed, timed waits")
    k[1].metric("Board within 10 min", f"{within10:.0%}")
    k[2].metric("Worst 10% wait at least", f"{c_all['wait_minutes'].quantile(.9):.0f} min")
    k[3].metric("Longest avg queue", f"{peak['mean_queue']:.0f}",
                help=f"{peak['stop_direction'].replace(' -> ', ' → ').title()} at {hh(peak['hour_slot'])}")
    k[4].metric("Often full (survey)", f"{SURVEY['failed_boarding'].isin(['Often', 'Always']).mean():.0%}",
                help="Survey: share of students answering 'often' or 'always'")

    with st.container(border=True):
        st.markdown("**In short**")
        md(f"""
- Most rides start quickly: the **typical wait is {c_all['wait_minutes'].median():.0f} minutes** and **{within10:.0%}** of passengers board within 10 minutes. But one passenger in ten waits **{c_all['wait_minutes'].quantile(.9):.0f} minutes or more**.
- The pain is concentrated. **{worst[0].title()} in the {dict(AM='morning', MD='midday', PM='evening')[worst[1]]}** averages **{worst_row['mean']:.0f} minutes**, and the **Bus Stop ↔ Campus Gate corridor** carries the biggest queues: up to **{peak['mean_queue']:.0f} people** waiting at {hh(peak['hour_slot'])}.
- In those peaks **more passengers arrive than there are seats leaving**, so queues can only grow. Elsewhere vehicles leave half-empty.
- Students *feel* waits are much longer than we measured, and **{SURVEY['tracking_app'].eq('Yes').mean():.0%} would use a vehicle-tracking app**.
""")

    # ---- 1. Why -----------------------------------------------------------
    st.markdown("## 1. Why we did this")
    md("""
Getting around OAU's campus depends on two kinds of shared vehicle: **CNG buses** (13 passengers) and **Keke** tricycles (5 passengers).
Students regularly complain about long queues, full vehicles driving past and arriving late to lectures, but those complaints are rarely backed by numbers.
We set out to measure the service directly and answer a set of concrete questions:

1. **Where and when** are waiting times longest?
2. How likely is a passenger to **board within 5, 10 and 15 minutes**?
3. When do queues **peak** at each stop, and how big do they get?
4. Do **mornings**, **Friday afternoons** and **weekends** behave differently?
5. Is the **CNG bus** experience different from **Keke**?
6. Is there **enough capacity**: are vehicles full, and are people left behind?
7. Does what **students report** match what we **observed**?
""")

    # ---- 2. Method ------------------------------------------------------
    st.markdown("## 2. How we collected the data")
    md(f"""
**Where.** Five boarding points: **Bus Stop, Campus Gate, Hall, New Market and SUB**. Several stops serve more than one direction, so we treated each
**stop + direction** (for example *Campus Gate → Bus Stop*) as its own route, giving **12 stop-directions**.

**When.** Every day from **Monday 26 October to Sunday 1 November 2026**, **08:00 to 18:00**, plus a few earlier sessions in late September.
We split each day into three blocks: **morning (before 11:00), midday (11:00–15:00) and evening (after 15:00)**.

**Who and how.** Everything was recorded **in person**: we physically went to each stop **in pairs of two** and took the records on the spot as things happened. Eight observers worked in four pairs on a **rotating rota**, so every pair covered all five stops and all three time blocks across the week.
Rotating meant no single observer's habits were tied to one stop.
""")
    st.markdown(
        """<div class='pipeline'>
        <div class='step'><b>1 · Observe</b><span>Pairs of observers physically at each stop, timing and counting on the spot</span></div><div class='arrow'>→</div>
        <div class='step'><b>2 · Enter</b><span>Sheets typed into one shared workbook (B1, B2, C, D)</span></div><div class='arrow'>→</div>
        <div class='step'><b>3 · Clean</b><span>Times put in 24-hour format, dates checked, blocks and routes derived</span></div><div class='arrow'>→</div>
        <div class='step'><b>4 · Analyse</b><span>Python (pandas, SciPy): summaries, confidence intervals, tests</span></div><div class='arrow'>→</div>
        <div class='step'><b>5 · Publish</b><span>This report and dashboard (Streamlit)</span></div>
        </div>""",
        unsafe_allow_html=True,
    )
    md("We used four record sheets and one survey:")
    cards = [
        ("B1 · Queue & demand", f"{len(Q_ALL):,} snapshots",
         "Every <b>10 minutes</b> the pair counted how many people were in the queue and how many <b>new people had joined</b> in the last 10 minutes. This measures <b>demand</b>."),
        ("B2 · Wait sample", f"{len(W_ALL):,} passengers",
         "The timer picked a passenger <b>as they joined the queue</b>, noted the clock time, and noted it again <b>when that person boarded</b>, plus which vehicle type they took. If they were still waiting when the session ended, the wait was marked <b>unfinished</b>."),
        ("C · Vehicle & trip", f"{len(V_ALL):,} vehicle arrivals",
         "For every vehicle that pulled in: its <b>vehicle ID</b>, <b>type</b>, <b>arrival and departure time</b>, how many <b>boarded</b>, how many <b>got off</b>, how many were <b>left behind</b> because it was full, and free seats on arrival. This measures <b>supply</b>."),
        ("Student survey", f"{len(SURVEY)} responses",
         "An online questionnaire on how students travel, how long they <i>feel</i> they wait, how often vehicles are full, fares, safety, comfort and what they want improved."),
    ]
    cols = st.columns(4)
    for col, (title, meta, body) in zip(cols, cards):
        col.markdown(f"<div class='sheet-card'><h4>{title}</h4><div class='meta'>{meta}</div><p>{body}</p></div>",
                     unsafe_allow_html=True)
    st.write("")
    md("""
A fourth field sheet (**D, fleet availability**: which vehicles were running, faulty or parked each day) was designed, but no records were collected for it, so it is not analysed.
In Week 4 we also started a **validation log**, writing down the predicted wait for a tagged passenger *before* timing them, to test a prediction model honestly.

**How the vehicle arrival times were captured.** Nothing here comes from GPS, an app or the operators: a pair of us stood at the stop and watched every vehicle in. Sheet C is the most detailed. Observers wrote down the clock time as a vehicle stopped (*Arrived*) and as it pulled away (*Departed*),
counted people stepping on (*Boarded*) and off (*Alighted*), and counted who was still standing in the queue when it left full (*Left behind*).
The chart below rebuilds one afternoon from those rows. Pick any date and route to see the raw record.
""")
    dates = sorted(V_ALL["Date"].dropna().dt.date.unique())
    dates = [d for d in dates if d >= pd.Timestamp("2026-10-26").date()] or dates
    a, b = st.columns([1, 2])
    d_sel = a.selectbox("Date", dates, index=min(3, len(dates) - 1), format_func=lambda d: f"{pd.Timestamp(d):%a %d %b}")
    routes = sorted(V_ALL["stop_direction"].dropna().unique())
    r_sel = b.selectbox("Stop → direction", routes, index=routes.index("BUS STOP -> CAMPUS GATE") if "BUS STOP -> CAMPUS GATE" in routes else 0)
    show(fig_vehicle_day(V_ALL, Q_ALL, d_sel, r_sel))
    explain(HOW["vday"],
            "On the default view (Bus Stop → Campus Gate, Thursday) vehicles arrive every few minutes, yet in the late afternoon almost every bus leaves full "
            "and a red bar appears under nearly every arrival, while the dotted queue line climbs. That pattern of full departures and a growing queue "
            "is the core problem this report documents.")

    # ---- 3. Metrics ----------------------------------------------------
    st.markdown("## 3. What we measured, and why")
    md("We chose measures that a passenger, a driver and a transport planner would each recognise. Each one answers a different part of the question *“is the service good enough?”*")
    st.markdown(
        """<table class='metrics'>
<tr><th>Measure</th><th>How we calculated it</th><th>Why we chose it</th></tr>
<tr><td>Waiting time</td><td>Time boarded − time joined, recomputed from the two clock times rather than trusting a typed-in total.</td><td>It is the experience passengers actually care about, and the clearest measure of service quality.</td></tr>
<tr><td>Typical (median) and worst-10% (90th percentile) wait</td><td>The middle value of all waits, and the wait that only 1 in 10 passengers exceeded.</td><td>Waits are lopsided: many people board at once, a few wait a very long time. An average alone hides both. The median shows a normal day; the 90th percentile shows a bad one.</td></tr>
<tr><td>Chance of boarding within 5 / 10 / 15 min</td><td>Share of timed passengers who boarded within the threshold, with a Wilson 95% confidence interval.</td><td>An easy-to-understand service standard (“will I make my 10-minute window to class?”), and comparable across stops.</td></tr>
<tr><td>Queue size and arrivals</td><td>People queuing at each 10-minute count; new arrivals per 10 minutes, scaled to an hour.</td><td>Shows <b>demand</b>: when and where people need transport.</td></tr>
<tr><td>Headway</td><td>Minutes between consecutive vehicle arrivals at the same stop-direction on the same day.</td><td>Shows <b>supply frequency</b>. Long gaps explain long waits even when vehicles are not full.</td></tr>
<tr><td>Load factor</td><td>Passengers boarded ÷ seats (CNG bus 13, Keke 5).</td><td>Tells us whether vehicles leave full (capacity is short) or half-empty (frequency or routing is the issue).</td></tr>
<tr><td>Left-behind share</td><td>Left behind ÷ (boarded + left behind), counted at each departure.</td><td>Direct evidence of unmet demand. A person missing two vehicles is counted twice, so we read it as how often vehicles leave people behind.</td></tr>
<tr><td>Demand-to-capacity ratio</td><td>Passengers arriving per hour ÷ seats departing per hour.</td><td>Above 1.0 the queue <i>must</i> grow. This pinpoints where extra vehicles would help most.</td></tr>
<tr><td>Survey perceptions</td><td>Share of students giving each answer; midpoints of the wait ranges they picked.</td><td>Puts the measurements next to how students experience the service.</td></tr>
</table>""",
        unsafe_allow_html=True,
    )

    # ---- 4. Decisions --------------------------------------------------
    st.markdown("## 4. Decisions we made along the way")
    md("""
- **Time blocks.** Morning = before 11:00, midday = 11:00–15:00, evening = from 15:00. These match the lecture day: the morning rush to class, the midday lull, the evening rush home.
- **Seat capacity.** Where a capacity was not written down we used **13 for a CNG bus and 5 for a Keke**.
- **Recalculated waits.** We worked out every wait from the *joined* and *boarded* times instead of using the typed “Wait (min)” column, so typing slips could not creep in. Rows where the boarding time came before the joining time were dropped.
- **Unfinished waits.** About **{u} passengers ({up:.0%})** were still waiting when observation ended. Their true wait is unknown, so averages use **completed waits only**. This makes our wait figures slightly optimistic.
- **Cleaning times and dates.** Times written in 12-hour format were converted to 24-hour; dates were read day-first (26/10/2026) and checked against the weekday written on the sheet.
- **Excluded rows.** A handful of rows had no destination recorded, or the same stop as origin and destination; we left them out so every result covers the 12 rota stop-directions.
- **Focus windows.** We compared **08:00–10:30** with the rest of the day (the morning lecture rush) and the Friday **13:00–14:30** window with the same window on other weekdays, because these were the specific peaks the team set out to test.
- **Statistical tests.** Waits and queues are lopsided, not bell-shaped, so we used tests that do not assume a normal distribution: **Mann–Whitney U** to compare two groups, **chi-square** for shares, **Spearman** for links between measures. We report **effect sizes and confidence intervals**, not just p-values. With thousands of rows almost any difference is “significant”; the effect size tells you whether it matters. Significance level 0.05.
""".format(u=int(W_ALL["censored"].sum()), up=W_ALL["censored"].mean()))

    # ---- 5. Findings ---------------------------------------------------
    st.markdown("## 5. What we found")

    st.markdown("### 5.1 Most waits are short, but some are very long")
    md(f"""
Over a third of passengers (**{c_all['wait_minutes'].eq(0).mean():.0%}**) boarded the moment they arrived, and the typical wait was **{c_all['wait_minutes'].median():.0f} minutes**.
But the distribution has a long tail: **{c_all['wait_minutes'].gt(20).mean():.0%}** of passengers waited more than 20 minutes.
Keke riders typically waited **{by_type.median()['Keke']:.0f} minute** against **{by_type.median()['CNG bus']:.0f} minutes** for CNG bus riders,
largely because a 5-seat Keke fills and leaves quickly while a bus waits to load.
""")
    a, b = st.columns(2)
    with a:
        show(fig_wait_hist(c_all))
        explain(HOW["hist"], f"A huge spike at zero minutes, mostly Keke riders who walked straight into a waiting tricycle, then a long, thin tail stretching past 30 minutes. That tail is where the complaints come from.")
    with b:
        show(fig_ecdf(c_all))
        explain(HOW["ecdf"], f"At the 10-minute mark the Keke line is at about {c_all[c_all['Type used'].eq('Keke')]['wait_minutes'].le(10).mean():.0%} and the CNG bus line at about {c_all[c_all['Type used'].eq('CNG bus')]['wait_minutes'].le(10).mean():.0%}. By 15 minutes the two have almost caught up.")

    st.markdown("### 5.2 Where waiting hurts most")
    md(f"""
Averages differ enormously by route. The worst single combination was **{worst[0].title()} in the {dict(AM='morning', MD='midday', PM='evening')[worst[1]]}**:
an average of **{worst_row['mean']:.1f} minutes** and a typical wait of **{worst_row['median']:.0f} minutes** across {int(worst_row['count']):,} timed passengers.
The Bus Stop ↔ Campus Gate corridor follows, in the direction of the rush: *towards* Bus Stop in the morning, *back to* Campus Gate in the evening.
""")
    show(fig_wait_by_route(c_all))
    explain(HOW["route"], "New Market → Academics stands out: its average is roughly double the next route, and its worst-10% tick sits beyond 30 minutes. Routes at the bottom (Campus Gate → Hall, Hall → Campus Gate) are effectively turn-up-and-go.")

    a, b = st.columns(2)
    with a:
        show(fig_block_box(c_all))
        explain(HOW["box"], f"Mornings are clearly worst (typical {by_block.median()['AM']:.0f} min), midday is easiest (typical {by_block.median()['MD']:.0f} min), and evenings sit between. The share boarding within 10 minutes falls from {within_block['MD']:.0%} at midday to {within_block['AM']:.0%} in the morning.")
    with b:
        show(fig_wait_by_hour(c_all))
        explain(HOW["hour"], "Waits are longest for people arriving between 08:00 and 10:00, ease off around midday, and rise again from mid-afternoon. CNG bus riders wait longer than Keke riders at almost every hour.")

    st.markdown("### 5.3 Will I get on within 10 minutes?")
    worst_ok = route_ok["mean"].idxmin()
    md(f"""
At six of the eleven stop-directions where we timed passengers, more than 85% of passengers board within 10 minutes. At **{worst_ok.title()}** it is closer to a coin toss:
only **{route_ok.loc[worst_ok, 'mean']:.0%}** board in that time. Use the slider to change the threshold.
""")
    thr = st.slider("Threshold (minutes)", 5, 20, 10, step=5, key="report_thr")
    show(fig_boarding(c_all, thr))
    explain(HOW["boarding"], f"Green-teal bars near 100% are reliable routes. The red-amber bars at the bottom (New Market → Academics and Bus Stop → Campus Gate) are where a student who leaves only 10 minutes to get somewhere is likely to be late.")

    st.markdown("### 5.4 When the queues build")
    md(f"""
Passengers keep arriving all day, and arrivals actually **rise** into the evening. Weekday stops see about **{daily.get(False, np.nan):,.0f}** new passengers a day across our routes,
against **{daily.get(True, np.nan):,.0f}** at weekends. The biggest average queue was **{peak['mean_queue']:.0f} people at {peak['stop_direction'].title()} around {hh(peak['hour_slot'])}**,
and individual counts there passed 100 people.
""")
    show(fig_queue_rhythm(Q_ALL))
    explain(HOW["rhythm"], "Demand has a small morning peak, dips around 11:00–12:00, then roughly doubles by 17:00. Queues follow the same shape: about 5 people at 08:00–10:00, under 2 at midday, then rising again to their highest at the end of the day, when supply falls furthest behind.")
    show(fig_queue_heat(Q_ALL))
    explain(HOW["heat"], "Two hot zones: Bus Stop → Campus Gate from 15:00 onwards (the trip off campus) and Campus Gate → Bus Stop in the morning (the trip in). New Market → Academics heats up in the morning. Most other rows stay pale all day.")
    a, b = st.columns(2)
    with a:
        show(fig_weekday_weekend(Q_ALL))
        explain(HOW["wkend"], "Weekday demand is around double weekend demand at almost every hour, and the weekday evening climb is much steeper.")
    with b:
        show(fig_friday(Q_ALL))
        explain(HOW["friday"], "At New Market the Friday early-afternoon queue is many times larger than on other weekdays. At Hall the difference is tiny in absolute terms (about one person).")

    st.markdown("### 5.5 Are there enough seats?")
    lf_type = vm.groupby("Type")["load"].mean()
    md(f"""
On average vehicles leave **{vm['load'].mean():.0%} full** (CNG bus {lf_type.get('CNG bus', np.nan):.0%}, Keke {lf_type.get('Keke', np.nan):.0%}), so on paper there is spare capacity.
But it is in the **wrong place at the wrong time**. On the Bus Stop → Campus Gate evening run, buses leave above 80% full and the left-behind share passes 70%.
About **{(vm['left_n'] > 0).mean():.0%}** of all departures left at least one person behind.
The clearest test is demand ÷ capacity: in **{len(over)} route-hours** more people arrived than there were seats departing, mostly **Bus Stop → Campus Gate from 15:00 to 18:00**
and **New Market → Academics at 08:00–10:00**.
""")
    a, b = st.columns(2)
    with a:
        show(fig_load(load))
        explain(HOW["load"], "Bus Stop → Campus Gate is the only route where vehicles routinely leave more than 80% full. Campus Gate → Bus Stop and New Market → Academics run at around 55–60%. Hall ↔ Campus Gate vehicles leave a quarter full or less: they mostly carry air.")
    with b:
        show(fig_left_behind(load))
        explain(HOW["left"], "The same routes leave the most people behind: Bus Stop → Campus Gate, New Market → Academics/Campus Gate and Campus Gate → Bus Stop. Elsewhere it is rare.")
    show(fig_dc(dc))
    explain(HOW["dc"], "The red cells sit exactly where the long queues are: the evening Bus Stop → Campus Gate run (peaking near 3 passengers per seat at 18:00) and the New Market → Academics morning. These are the hours where adding vehicles would pay off most.")
    show(fig_headway(headway))
    explain(HOW["headway"], "Busy corridors like Campus Gate → Bus Stop see a vehicle every 2–3 minutes, so their problem is capacity, not frequency. Quieter routes such as SUB → Hall or Campus Gate → New Market can wait 6–10 minutes between vehicles, which explains waits there even when vehicles leave half-empty.")

    st.markdown("### 5.6 What students told us")
    md(f"""
**{len(SURVEY)}** students answered the survey. Most (**{SURVEY['transport_used'].eq('Either').mean():.0%}**) use whichever vehicle comes first, but **{SURVEY['transport_preference'].eq('Keke').mean():.0%}** would rather take a Keke.
**{SURVEY['failed_boarding'].isin(['Often', 'Always']).mean():.0%}** say the first vehicle is *often* or *always* too full to board, and the top requests are
**shorter waits and more vehicles**. Asked about a tracking app, **{SURVEY['tracking_app'].eq('Yes').mean():.0%} said yes**.
""")
    a, b = st.columns(2)
    with a:
        show(fig_survey_bar(SURVEY, "typical_wait", "“How long do you usually wait?”", SURVEY_ORDERS["typical_wait"]))
        explain(HOW["survey"], "Students most often say 6–10 minutes, but over half pick 11 minutes or more, far longer than the typical 3 minutes we measured.")
    with b:
        show(fig_multi(SURVEY, "desired_improvements", "“What would you most like to see improved?”"))
        explain("Each bar counts how many of the students ticked that improvement; the label is the share of all respondents.",
                "Shorter waits and more vehicles lead, followed by more drivers and lower fares: demands about capacity, not comfort.")
    show(fig_perceived(COMPARE))
    explain(HOW["perceived"], "At every stop students report longer waits than we timed, by roughly 2½ times at Campus Gate, 3½ times at SUB and 7 times at Hall. Part of this is how waiting feels (uncertain waits feel longer), part is that people remember the bad days, and part is the small survey samples per stop (2–19 students).")

    st.markdown("### 5.7 Are the differences real? The statistics")
    md("""
Every comparison above was tested formally. All of the headline differences are statistically significant, but significance alone says little with thousands of rows, so the chart shows **how big** each difference is.
By common rules of thumb an effect size of 0.1 is small, 0.3 medium and 0.5 large.
""")
    if not TESTS.empty:
        show(fig_effects(TESTS))
        explain(HOW["effects"], "The largest effects are the Friday New Market surge (0.83), the morning penalty at New Market and Hall (about 0.5) and weekday vs weekend demand (0.40). The Keke vs CNG bus gap is real but small to medium (0.26). The morning Campus Gate → Bus Stop queue is smaller than the evening return queue (negative value).")
        nice = TESTS[["question", "test_name", "test", "n_group_1", "n_group_2", "p_value", "effect_size", "effect_size_name", "decision_at_0_05"]]
        with st.expander("Full test table"):
            st.dataframe(nice, hide_index=True, width="stretch",
                         column_config={"p_value": st.column_config.NumberColumn("p-value", format="%.1e"),
                                        "effect_size": st.column_config.NumberColumn("effect", format="%.2f")})
    if not SPEARMAN.empty:
        show(fig_spearman(SPEARMAN))
        explain(HOW["spearman"], "Queue size is strongly linked with waiting time (0.77) and with how full vehicles leave (0.79): long queues mean long waits and packed vehicles. Arrivals and headway move in opposite directions (−0.57): where demand is high, operators already send vehicles more often.")

    # ---- 6. Limitations ------------------------------------------------
    st.markdown("## 6. Limitations: what this study can’t tell you")
    callout(
        "<b>Estimated rows.</b> The observation workbook notes that some rows were <b>model-estimated</b> to fill in times and stops the field team could not cover. "
        "The file we analysed does not mark which rows those are, so we could not separate them. The results describe the combined dataset, "
        "and the field-only figures may differ.", warn=True)
    md(f"""
- **One week of main fieldwork.** 26 October – 1 November 2026 may not represent exam periods, holidays, fuel scarcity or the start of a semester.
- **Five stops, 08:00–18:00.** Early-morning and late-evening travel, and routes we did not cover, are outside the data.
- **Unfinished waits** ({int(W_ALL['censored'].sum())} passengers) were excluded because we did not record how long they had waited when observation stopped. True waits are therefore slightly longer than reported, and a survival analysis (which handles unfinished waits properly) was not possible.
- **Observations are not fully independent.** Passengers in the same queue share the same fate, which makes p-values look stronger than they are. We lean on effect sizes for that reason.
- **Left-behind counts** can count the same person more than once if they miss several vehicles.
- **No fleet data.** Sheet D (vehicles running vs faulty) was never filled in, so we cannot say whether low supply comes from fewer vehicles operating or from where they are deployed.
- **Small, self-selected survey.** {len(SURVEY)} students answered online. Per-stop survey samples are as small as 2, so the perceived-vs-measured comparison is descriptive only.
- **Prediction model not validated.** The Week 4 validation log holds only one complete prediction, so we make no claims about forecasting waits.
- **Human timing.** Clock times were recorded to the minute, so very short waits are rounded and two observers may count a crowded queue slightly differently.
""")

    # ---- 7. Conclusion ---------------------------------------------------
    st.markdown("## 7. Conclusion and recommendations")
    md(f"""
OAU campus transport works well **most of the time and on most routes**: a typical passenger boards in about {c_all['wait_minutes'].median():.0f} minutes.
The problem is **concentrated and predictable**. It is the **evening Bus Stop → Campus Gate run**, the **morning Campus Gate → Bus Stop and New Market → Academics runs**, and **Friday early afternoon at New Market**.
At those times more students arrive than there are seats, so queues grow and vehicles leave people behind, while vehicles elsewhere run nearly empty.
Students feel the bad moments far more strongly than the averages suggest.

**What we recommend:**
1. **Move vehicles, not just add them.** Shift buses from low-load routes (Hall ↔ Campus Gate vehicles leave about a quarter full or less) to the Bus Stop → Campus Gate evening run (15:00–18:00) and New Market → Academics in the morning (08:00–10:30).
2. **Add peak-only capacity** on the corridor where demand exceeds seats, e.g. extra CNG buses scheduled for 15:00–18:00 on weekdays.
3. **Prepare for Fridays** at New Market in the 13:00–14:30 window.
4. **Publish real-time information.** With {SURVEY['tracking_app'].eq('Yes').mean():.0%} of students willing to use a tracking app, showing where vehicles are would cut the *uncertainty* that makes waits feel long, even before any new vehicles arrive.
5. **Keep measuring.** Fill in the fleet sheet, record how long unfinished waits had lasted, mark observed vs estimated rows, and repeat the study in a different month to check that the patterns hold.
""")

    # ---- 8. Team ---------------------------------------------------------
    st.markdown("## 8. Who did what")
    team_cards()
    md("The <b>Dashboard</b> page lets you filter every chart by date, stop, direction, time block and vehicle type. The <b>Data</b> page lets you download the records behind them.")


def team_cards() -> None:
    if TEAM.empty:
        st.info("Add team members to team.csv.")
        return
    rows = list(TEAM.iterrows())
    for start in range(0, len(rows), 4):
      cols = st.columns(4)
      for col, (_, r) in zip(cols, rows[start:start + 4]):
        initials = "".join(p[0] for p in str(r["name"]).split()[:2]).upper()
        col.markdown(
            f"<div class='team-card'><div class='avatar'>{initials}</div><div class='nm'>{r['name']}</div>"
            f"<div class='rl'>{r['role']}</div><div class='ct'>{r['contributions']}</div></div>",
            unsafe_allow_html=True,
        )


# ==========================================================================
# PAGE 2: DASHBOARD (filters)
# ==========================================================================
def page_dashboard() -> None:
    q_all, w_all, v_all = Q_ALL, W_ALL, V_ALL
    sb = st.sidebar
    sb.markdown("### Filters")
    sb.caption("Every chart on this page recalculates for your selection.")
    dates = pd.concat([q_all["Date"], w_all["Date"], v_all["Date"]]).dropna()
    dmin, dmax = dates.min().date(), dates.max().date()
    rng = sb.date_input("Date range", value=(dmin, dmax), min_value=dmin, max_value=dmax)
    d_from, d_to = rng if isinstance(rng, tuple) and len(rng) == 2 else (dmin, dmax)
    days = sb.multiselect("Day of week", DAY_ORDER, default=DAY_ORDER)
    blocks = sb.multiselect("Time block", ["AM", "MD", "PM"], default=["AM", "MD", "PM"],
                            help="AM before 11:00 · MD 11:00–15:00 · PM from 15:00")
    stops = sorted(set(q_all["Stop"].dropna()) | set(w_all["Stop"].dropna()))
    sel_stops = sb.multiselect("Boarding stop", stops, default=stops)
    routes = sorted(r for r in set(q_all["stop_direction"]) | set(w_all["stop_direction"]) | set(v_all["stop_direction"])
                    if isinstance(r, str) and r.split(" -> ")[0] in sel_stops)
    sel_routes = sb.multiselect("Stop → direction", routes, default=routes)
    types = sb.multiselect("Vehicle type", ["CNG bus", "Keke"], default=["CNG bus", "Keke"])
    hours = sb.slider("Hour of day", 8, 18, (8, 18))

    def filt(f: pd.DataFrame, type_col: str | None = None) -> pd.DataFrame:
        m = (f["Date"].dt.date.between(d_from, d_to) & f["Day"].isin(days) & f["Block"].isin(blocks)
             & f["stop_direction"].isin(sel_routes) & f["hour"].between(hours[0], hours[1] + .999))
        if type_col:
            m &= f[type_col].isin(types)
        return f.loc[m.fillna(False)]

    q, w, v = filt(q_all), filt(w_all, "Type used"), filt(v_all, "Type")
    c = completed(w)
    sb.divider()
    sb.caption(f"**In view:** {len(q):,} queue counts · {len(w):,} timed passengers · {len(v):,} vehicle arrivals")

    st.markdown("<div class='kicker'>Interactive dashboard</div>", unsafe_allow_html=True)
    st.markdown("# Explore the data")
    st.markdown("<div class='dek' style='font-size:1.08rem'>Use the filters on the left to focus on a stop, a day or a time of day. "
                "Every chart has a short guide underneath explaining how to read it.</div>", unsafe_allow_html=True)
    st.write("")

    if c.empty and q.empty and v.empty:
        st.warning("Nothing matches these filters. Widen the selection in the sidebar.")
        return

    vm = vehicle_metrics(v)
    k = st.columns(6)
    k[0].metric("Timed waits", f"{len(c):,}", help=f"{int(w['censored'].sum()):,} unfinished waits excluded")
    k[1].metric("Typical wait", f"{c['wait_minutes'].median():.0f} min" if len(c) else "—")
    k[2].metric("Worst 10%", f"{c['wait_minutes'].quantile(.9):.0f} min" if len(c) else "—")
    k[3].metric("Board ≤ 10 min", f"{c['wait_minutes'].le(10).mean():.0%}" if len(c) else "—")
    k[4].metric("Seats filled", f"{vm['load'].mean():.0%}" if len(vm) else "—")
    k[5].metric("Left someone", f"{(vm['left_n'] > 0).mean():.0%}" if len(vm) else "—",
                help="Share of vehicle departures that left at least one person behind")

    tabs = st.tabs(["⏱️ Waiting", "👥 Queues & demand", "🚐 Vehicles & capacity", "📝 Survey", "🧪 Statistics"])
    with tabs[0]:
        if c.empty:
            st.info("No completed waits in this selection.")
        else:
            show(fig_wait_by_route(c)); explain(HOW["route"], "Longest bars = stop-directions where people wait longest. A red tick far to the right of its bar means waits there are unpredictable.")
            thr = st.slider("Boarding threshold (minutes)", 1, 30, 10, key="dash_thr")
            show(fig_boarding(c, thr)); explain(HOW["boarding"], "Routes near the bottom are the least reliable for your chosen threshold. Try 5 and 15 minutes to see which routes are fine only if you leave extra time.")
            a, b = st.columns(2)
            with a:
                show(fig_wait_hist(c)); explain(HOW["hist"], "A tall bar at zero with a long tail to the right means service is usually instant but occasionally very slow.")
                show(fig_block_box(c)); explain(HOW["box"], "Compare the height of the boxes to see which part of the day is worst for your selection.")
            with b:
                show(fig_ecdf(c)); explain(HOW["ecdf"], "The gap between the two lines at 10 minutes is the advantage of one vehicle type over the other.")
                show(fig_wait_by_hour(c)); explain(HOW["hour"], "Peaks show the hours to avoid; dips show when to travel.")
            with st.expander("Summary table"):
                s = (c.groupby(["stop_direction", "Block"])["wait_minutes"]
                     .agg(n="count", mean="mean", median="median", p90=lambda x: x.quantile(.9)).reset_index()
                     .sort_values("mean", ascending=False))
                st.dataframe(s, hide_index=True, width="stretch", column_config={
                    "stop_direction": "Stop → direction", "n": "Passengers",
                    "mean": st.column_config.ProgressColumn("Average (min)", format="%.1f", min_value=0, max_value=float(s["mean"].max() or 1)),
                    "median": st.column_config.NumberColumn("Typical", format="%.0f"),
                    "p90": st.column_config.NumberColumn("Worst 10%", format="%.0f")})
    with tabs[1]:
        if q.empty:
            st.info("No queue counts in this selection.")
        else:
            show(fig_queue_rhythm(q)); explain(HOW["rhythm"], "If the teal line climbs while the bars stay flat, vehicles are falling behind demand.")
            show(fig_queue_heat(q)); explain(HOW["heat"], "Dark-red squares are the stop-hours to avoid, or where more vehicles are needed.")
            per = queue_by_route_hour(q)
            top = per.groupby("stop_direction")["mean_queue"].max().sort_values(ascending=False).index.tolist()
            pick = st.multiselect("Routes to compare", top, default=top[:4])
            show(fig_rush(q, pick)); explain(HOW["rush"], "The peak of each line is that route's rush hour.")
            a, b = st.columns(2)
            with a:
                show(fig_weekday_weekend(q)); explain(HOW["wkend"], "The gap between the lines is how much quieter weekends are.")
            with b:
                byday = q.groupby("Day")["Queue size"].mean().reindex(DAY_ORDER).dropna().reset_index()
                fig = px.bar(byday, x="Day", y="Queue size", color="Queue size", color_continuous_scale="YlOrRd",
                             labels={"Queue size": "average queue", "Day": ""})
                fig.update_layout(coloraxis_showscale=False)
                show(style(fig, 400, "Average queue by day of week"))
                explain("Each bar is the average queue size across all counts on that weekday.", "Taller bars = busier days for your selection.")
    with tabs[2]:
        if v.empty:
            st.info("No vehicle records in this selection.")
        else:
            headway, load, dc = D.vehicle_efficiency(q, v)
            load = load.dropna(subset=["Type"])
            a, b = st.columns(2)
            with a:
                show(fig_load(load)); explain(HOW["load"], "Bars near the dotted line mean vehicles leave full; short bars mean spare seats.")
            with b:
                show(fig_left_behind(load)); explain(HOW["left"], "Long bars mark where full vehicles regularly leave people standing.")
            show(fig_dc(dc)); explain(HOW["dc"], "Red squares are where demand outstrips supply.")
            show(fig_headway(headway)); explain(HOW["headway"], "Dark squares = long gaps between vehicles.")
            vdates = sorted(v["Date"].dropna().dt.date.unique())
            vroutes = sorted(v["stop_direction"].dropna().unique())
            a, b = st.columns([1, 2])
            dsel = a.selectbox("Date", vdates, index=len(vdates) - 1, format_func=lambda d: f"{pd.Timestamp(d):%a %d %b}", key="vd")
            rsel = b.selectbox("Stop → direction", vroutes, key="vr")
            show(fig_vehicle_day(v, q, dsel, rsel)); explain(HOW["vday"], "Clusters of red bars show when vehicles were leaving full.")
    with tabs[3]:
        a, b = st.columns([1, 1])
        with a:
            col = st.selectbox("Survey question", list(SURVEY_Q), format_func=SURVEY_Q.get)
            show(fig_survey_bar(SURVEY.dropna(subset=[col]), col, SURVEY_Q[col], SURVEY_ORDERS.get(col)))
            explain(HOW["survey"], "Longer bars are more common answers.")
        with b:
            show(fig_multi(SURVEY, "preference_reasons", "Why students prefer their transport type"))
            explain("Each bar counts students who ticked that reason.", "Comfort comes first, followed by going directly to the destination, shorter waits and faster journeys.")
        show(fig_perceived(COMPARE)); explain(HOW["perceived"], "Amber taller than teal = students feel waits are longer than we measured.")
        comments = SURVEY["other_comments"].dropna()
        comments = comments[comments.str.len() > 3]
        with st.expander(f"Read the students' own comments ({len(comments)})"):
            for t in comments:
                st.markdown(f"> {t}")
    with tabs[4]:
        st.caption("Tests use the full dataset and do not change with the filters.")
        if not TESTS.empty:
            show(fig_effects(TESTS)); explain(HOW["effects"], "Dots far from zero with bars that don't cross zero are the strongest, most certain differences.")
        if not SPEARMAN.empty:
            show(fig_spearman(SPEARMAN)); explain(HOW["spearman"], "Look for dark squares: those pairs of measures are tightly linked.")


# ==========================================================================
# PAGE 3: DATA
# ==========================================================================
def page_data() -> None:
    st.markdown("<div class='kicker'>Open data</div>", unsafe_allow_html=True)
    st.markdown("# The records behind the report")
    md("All field records as analysed (after cleaning). Filter in the table header, or download a sheet as CSV.")
    choice = st.radio("Dataset", ["B2 · Timed passengers", "B1 · Queue counts", "C · Vehicle arrivals", "Student survey"], horizontal=True)
    df = {"B2 · Timed passengers": W_ALL, "B1 · Queue counts": Q_ALL, "C · Vehicle arrivals": V_ALL, "Student survey": SURVEY}[choice]
    drop = [c for c in df.columns if c.endswith(" minutes") or c in
            ("Date_original", "time_of_day", "date_day_mismatch", "is_weekend", "valid_route", "joined_minutes",
             "boarded_minutes", "censor_time_available", "end_before_start", "hour")]
    view = df.drop(columns=drop)
    st.caption(f"{len(view):,} rows")
    st.dataframe(view, width="stretch", height=560, hide_index=True)
    st.download_button("⬇️ Download as CSV", view.to_csv(index=False).encode("utf-8"),
                       file_name=choice.split(" · ")[1].lower().replace(" ", "_") + ".csv", mime="text/csv")


def page_team() -> None:
    st.markdown("<div class='kicker'>Credits</div>", unsafe_allow_html=True)
    st.markdown("# The team")
    md("This study was designed, carried out and analysed by the following people.")
    team_cards()


nav = st.navigation(
    [
        st.Page(page_report, title="Report", icon="📖", default=True),
        st.Page(page_dashboard, title="Dashboard", icon="📊", url_path="dashboard"),
        st.Page(page_data, title="Data", icon="🗂️", url_path="data"),
        st.Page(page_team, title="Team", icon="👥", url_path="team"),
    ],
    position="top",
)
nav.run()
footer()
