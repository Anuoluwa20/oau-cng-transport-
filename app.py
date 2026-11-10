"""Interactive Streamlit dashboard for the OAU campus transport (CNG / Keke) study.

Run from the project root:

    pip install -r requirements.txt
    streamlit run app.py

All data files must sit in the same folder as this app.py (no subfolders).
"""

from __future__ import annotations

import contextlib
import io
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Data helpers (copied from the project's src/ package so this file is standalone)
# ---------------------------------------------------------------------------
import math
from datetime import datetime, time
from typing import Any

HERE = Path(__file__).resolve().parent
CAPACITIES = {"CNG bus": 13, "Keke": 5}
SHEET_CONFIG = {
    "queue": {"csv": "B1_Queue_and_Demand.csv", "event_time": "Time"},
    "wait": {"csv": "B2_Wait_Sample.csv", "event_time": "Time joined"},
    "vehicle": {"csv": "C_Vehicle_and_Trip.csv", "event_time": "Arrived"},
}


def read_csv_sheet(name: str) -> pd.DataFrame:
    path = HERE / name
    try:
        frame = pd.read_csv(path, header=3, encoding="utf-8-sig")
    except UnicodeDecodeError:
        frame = pd.read_csv(path, header=3, encoding="cp1252")
    frame.columns = [str(c).strip() for c in frame.columns]
    return frame.dropna(how="all").reset_index(drop=True)


def load_all_data() -> dict[str, pd.DataFrame]:
    return {
        key: normalize_frame(key, read_csv_sheet(cfg["csv"]))
        for key, cfg in SHEET_CONFIG.items()
    }


def parse_clock(value: Any) -> float:
    """Convert a time-like value to minutes since midnight."""
    if pd.isna(value):
        return np.nan
    if isinstance(value, time):
        return value.hour * 60 + value.minute + value.second / 60
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.hour * 60 + value.minute + value.second / 60
    text = str(value).strip()
    for fmt in ("%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M:%S %p"):
        try:
            parsed = datetime.strptime(text, fmt).time()
            return parsed.hour * 60 + parsed.minute + parsed.second / 60
        except ValueError:
            continue
    return np.nan


def parse_date_column(frame: pd.DataFrame) -> pd.DataFrame:
    """Parse dates day-first while retaining invalid/missing values as NaT."""
    if "Date" in frame.columns:
        frame["Date_original"] = frame["Date"].astype("string")
        frame["Date"] = pd.to_datetime(frame["Date"], dayfirst=True, errors="coerce")
    return frame


def derive_block(hour: pd.Series) -> pd.Series:
    """Assign the configured AM, MD and PM blocks from numeric hours."""
    conditions = [
        hour.lt(11),
        hour.ge(11) & hour.lt(15),
        hour.ge(15),
    ]
    return pd.Series(
        np.select(conditions, ["AM", "MD", "PM"], default=None),
        index=hour.index,
        dtype="string",
    )


def normalize_frame(sheet_key: str, frame: pd.DataFrame) -> pd.DataFrame:
    """Add normalized date, time, hour, block, route and source fields."""
    frame = parse_date_column(frame)
    event_time = SHEET_CONFIG[sheet_key]["event_time"]
    time_columns = {
        column
        for column in (event_time, "Time joined", "Time boarded", "Arrived", "Departed")
        if column and column in frame.columns
    }
    for column in time_columns:
        frame[f"{column} minutes"] = frame[column].map(parse_clock).astype("float64")
    if event_time and event_time in frame.columns:
        minutes = frame[f"{event_time} minutes"]
        frame["hour"] = minutes / 60.0
        derived_block = derive_block(frame["hour"])
        frame["Block"] = derived_block.fillna(
            frame.get("Block", pd.Series(pd.NA, index=frame.index, dtype="string"))
            .astype("string")
            .str.upper()
        )
        frame["time_of_day"] = pd.to_datetime(
            minutes, unit="m", origin="1899-12-30", errors="coerce"
        ).dt.time
    else:
        frame["hour"] = np.nan
        frame["time_of_day"] = pd.Series(
            pd.NA, index=frame.index, dtype="object"
        )
    if "Day" in frame.columns:
        frame["Day"] = frame["Day"].astype("string").str.strip().str.title()
    if "Stop" in frame.columns and "Destination / direction" in frame.columns:
        stop = frame["Stop"].astype("string").str.strip()
        destination = frame["Destination / direction"].astype("string").str.strip()
        frame["stop_direction"] = stop.fillna("Unknown stop") + " -> " + destination.fillna(
            "Unknown destination"
        )
    if "Date" in frame.columns and "Day" in frame.columns:
        parsed_day = frame["Date"].dt.day_name()
        frame["date_day_mismatch"] = (
            frame["Date"].notna()
            & frame["Day"].notna()
            & parsed_day.ne(frame["Day"])
        )
    else:
        frame["date_day_mismatch"] = False
    return frame


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    """Return a numeric column, or an all-missing series when absent."""
    if column not in frame.columns:
        return pd.Series(np.nan, index=frame.index, dtype="float64")
    return pd.to_numeric(frame[column], errors="coerce")


def prepare_wait_data(wait: pd.DataFrame) -> pd.DataFrame:
    """Recompute waits from joined/boarded clocks and keep censoring explicit."""
    frame = wait.copy()
    joined = frame.get("Time joined", pd.Series(pd.NA, index=frame.index)).map(
        parse_clock
    )
    boarded = frame.get("Time boarded", pd.Series(pd.NA, index=frame.index)).map(
        parse_clock
    )
    frame["joined_minutes"] = pd.to_numeric(joined, errors="coerce")
    frame["boarded_minutes"] = pd.to_numeric(boarded, errors="coerce")
    frame["end_before_start"] = (
        frame["boarded_minutes"].notna()
        & frame["joined_minutes"].notna()
        & frame["boarded_minutes"].lt(frame["joined_minutes"])
    )
    unfinished = pd.Series(False, index=frame.index)
    if "Unfinished?" in frame.columns:
        unfinished = (
            frame["Unfinished?"]
            .astype("string")
            .str.strip()
            .str.casefold()
            .isin({"yes", "true", "1"})
        )
    frame["censored"] = frame["boarded_minutes"].isna() | unfinished
    frame["wait_minutes"] = frame["boarded_minutes"] - frame["joined_minutes"]
    invalid = frame["end_before_start"] | frame["joined_minutes"].isna()
    frame.loc[frame["censored"] | invalid, "wait_minutes"] = np.nan
    frame.loc[frame["wait_minutes"].lt(0), "wait_minutes"] = np.nan
    frame["wait_event"] = frame["wait_minutes"].notna()
    frame["censor_time_available"] = False
    if "Type used" in frame.columns:
        normalized_type = (
            frame["Type used"].astype("string").str.strip().str.casefold()
        )
        frame["Type used"] = normalized_type.map(
            {"cng bus": "CNG bus", "keke": "Keke"}
        ).fillna(frame["Type used"])
    return frame


def wilson_interval(successes: int, total: int) -> tuple[float, float]:
    """Compute a Wilson 95% confidence interval for a proportion."""
    if total == 0:
        return np.nan, np.nan
    z = 1.959963984540054
    proportion = successes / total
    denominator = 1 + z**2 / total
    center = (proportion + z**2 / (2 * total)) / denominator
    margin = (
        z
        * math.sqrt(
            proportion * (1 - proportion) / total + z**2 / (4 * total**2)
        )
        / denominator
    )
    return max(0.0, center - margin), min(1.0, center + margin)


def vehicle_efficiency(
    queue: pd.DataFrame, vehicle: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Compute headway, route load/left-behind, and demand-capacity metrics."""
    vehicles = vehicle.copy()
    vehicles["arrived_minutes"] = vehicles.get(
        "Arrived minutes", pd.Series(np.nan, index=vehicles.index)
    )
    vehicles["capacity_numeric"] = _numeric(vehicles, "Capacity")
    if "Type" in vehicles.columns:
        type_capacity = (
            vehicles["Type"].astype("string").str.strip().str.casefold().map(
                {"cng bus": CAPACITIES["CNG bus"], "keke": CAPACITIES["Keke"]}
            )
        )
        vehicles["capacity_numeric"] = vehicles["capacity_numeric"].fillna(
            type_capacity
        )
    vehicles["boarded_numeric"] = _numeric(vehicles, "Boarded")
    vehicles["left_behind_numeric"] = _numeric(vehicles, "Left behind")
    vehicles["load_factor"] = (
        vehicles["boarded_numeric"] / vehicles["capacity_numeric"]
    )
    vehicles["hour_slot"] = np.floor(vehicles["hour"])
    vehicles["headway_min"] = vehicles.sort_values(
        ["Date", "stop_direction", "arrived_minutes"]
    ).groupby(["Date", "stop_direction"], dropna=False)["arrived_minutes"].diff()
    vehicles.loc[vehicles["headway_min"].le(0), "headway_min"] = np.nan

    headway = (
        vehicles.groupby(["stop_direction", "hour_slot"], dropna=False)
        .agg(
            mean_headway_min=("headway_min", "mean"),
            median_headway_min=("headway_min", "median"),
            n=("headway_min", "count"),
        )
        .reset_index()
    )
    load = (
        vehicles.groupby(["stop_direction", "Type"], dropna=False)
        .agg(
            mean_load_factor=("load_factor", "mean"),
            boarded_total=("boarded_numeric", "sum"),
            capacity_total=("capacity_numeric", "sum"),
            left_behind_total=("left_behind_numeric", "sum"),
            n=("Vehicle ID", "count"),
        )
        .reset_index()
    )
    load["left_behind_rate"] = load["left_behind_total"] / (
        load["boarded_total"] + load["left_behind_total"]
    )
    load["load_factor_pct"] = load["mean_load_factor"] * 100

    queue_hour = queue.copy()
    queue_hour["hour_slot"] = np.floor(queue_hour["hour"])
    queue_hour["arrivals_numeric"] = _numeric(queue_hour, "New arrivals (10 min)")
    arrivals = (
        queue_hour.groupby(["Date", "stop_direction", "hour_slot"], dropna=False)
        .agg(arrivals_per_hour=("arrivals_numeric", "sum"))
        .reset_index()
        .groupby(["stop_direction", "hour_slot"], dropna=False)
        .agg(
            demand_per_hour=("arrivals_per_hour", "mean"),
            demand_n=("arrivals_per_hour", "count"),
        )
        .reset_index()
    )
    departed_minutes = vehicles.get(
        "Departed minutes", pd.Series(np.nan, index=vehicles.index)
    )
    vehicles["departed_hour_slot"] = np.floor(
        pd.to_numeric(departed_minutes, errors="coerce") / 60
    )
    vehicles["departed_capacity"] = vehicles["capacity_numeric"].where(
        pd.to_numeric(departed_minutes, errors="coerce").notna(), np.nan
    )
    capacity = (
        vehicles.groupby(
            ["Date", "stop_direction", "departed_hour_slot"], dropna=False
        )
        .agg(capacity_per_hour=("departed_capacity", "sum"))
        .reset_index()
        .rename(columns={"departed_hour_slot": "hour_slot"})
        .groupby(["stop_direction", "hour_slot"], dropna=False)
        .agg(
            seats_leaving_per_hour=("capacity_per_hour", "mean"),
            capacity_n=("capacity_per_hour", "count"),
        )
        .reset_index()
    )
    demand_capacity = arrivals.merge(
        capacity, on=["stop_direction", "hour_slot"], how="outer"
    )
    demand_capacity["demand_to_capacity_ratio"] = (
        demand_capacity["demand_per_hour"]
        / demand_capacity["seats_leaving_per_hour"].replace(0, np.nan)
    )
    demand_capacity["n"] = demand_capacity[["demand_n", "capacity_n"]].max(axis=1)
    return headway, load, demand_capacity



st.set_page_config(
    page_title="OAU Campus Transport Dashboard",
    page_icon="🚌",
    layout="wide",
)

# --------------------------------------------------------------------------
# Styling
# --------------------------------------------------------------------------
TYPE_COLORS = {"CNG bus": "#1f6f78", "Keke": "#e0a100"}
BLOCK_COLORS = {"AM": "#3b7dd8", "MD": "#8a63d2", "PM": "#d9534f"}
SEQ_SCALE = "YlOrRd"
DAY_ORDER = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
]
PLOT_LAYOUT = dict(
    template="plotly_white",
    margin=dict(l=10, r=10, t=90, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0, title_text=""),
    font=dict(size=13),
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.6rem;}
      div[data-testid="stMetric"] {
          background: rgba(31,111,120,0.06);
          border: 1px solid rgba(31,111,120,0.18);
          border-radius: 10px; padding: 10px 14px;
      }
      div[data-testid="stMetricLabel"] p {font-size: 0.85rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


def style(fig: go.Figure, height: int = 420, title: str | None = None) -> go.Figure:
    fig.update_layout(height=height, **PLOT_LAYOUT)
    if title:
        fig.update_layout(title=dict(text=title, x=0, y=0.97, yanchor="top", yref="container", font=dict(size=16)))
    return fig


def hour_label(h: float) -> str:
    return f"{int(h):02d}:00" if pd.notna(h) else "—"


# --------------------------------------------------------------------------
# Data loading (cached)
# --------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading observation workbook…")
def load_frames() -> dict[str, pd.DataFrame]:
    frames = load_all_data()
    wait = prepare_wait_data(frames["wait"])
    for key in ("queue", "vehicle"):
        frames[key]["hour_slot"] = np.floor(frames[key]["hour"])
    wait["hour_slot"] = np.floor(wait["hour"])
    frames["wait"] = wait
    if "Type" in frames["vehicle"]:
        frames["vehicle"]["Type"] = (
            frames["vehicle"]["Type"].astype("string").str.strip()
        )
    for key in ("queue", "wait", "vehicle"):
        f = frames[key]
        f["Day"] = f["Day"].fillna(f["Date"].dt.day_name())
        f["is_weekend"] = f["Day"].isin(["Saturday", "Sunday"])
        # pandas/pyarrow string dtype -> plain object for widget compatibility
        for col in ("stop_direction", "Block", "Day", "Stop"):
            if col in f:
                f[col] = f[col].astype(object)
    return frames


@st.cache_data
def load_table(name: str) -> pd.DataFrame:
    path = HERE / name
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


@st.cache_data
def load_survey() -> pd.DataFrame:
    path = HERE / "survey_clean.csv"
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


frames = load_frames()
queue_all, wait_all, vehicle_all = frames["queue"], frames["wait"], frames["vehicle"]

# --------------------------------------------------------------------------
# Sidebar filters
# --------------------------------------------------------------------------
st.sidebar.title("🚌 Filters")
st.sidebar.caption("Filters apply to every observation tab.")

all_dates = pd.concat(
    [queue_all["Date"], wait_all["Date"], vehicle_all["Date"]]
).dropna()
dmin, dmax = all_dates.min().date(), all_dates.max().date()
date_range = st.sidebar.date_input(
    "Date range", value=(dmin, dmax), min_value=dmin, max_value=dmax
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    d_from, d_to = date_range
else:
    d_from, d_to = dmin, dmax

days = st.sidebar.multiselect("Day of week", DAY_ORDER, default=DAY_ORDER)
blocks = st.sidebar.multiselect(
    "Time block", ["AM", "MD", "PM"], default=["AM", "MD", "PM"],
    help="AM before 11:00 · MD 11:00–15:00 · PM from 15:00",
)
stops = sorted(
    set(queue_all["Stop"].dropna()) | set(wait_all["Stop"].dropna())
    | set(vehicle_all["Stop"].dropna())
)
sel_stops = st.sidebar.multiselect("Boarding stop", stops, default=stops)
route_options = sorted(
    r for r in set(queue_all["stop_direction"].dropna())
    | set(wait_all["stop_direction"].dropna())
    | set(vehicle_all["stop_direction"].dropna())
    if r.split(" -> ")[0] in sel_stops
)
sel_routes = st.sidebar.multiselect(
    "Stop → direction", route_options,
    default=[r for r in route_options if "Unknown" not in r],
    help="Rows with a missing destination are left out by default.",
)
types = st.sidebar.multiselect(
    "Vehicle type", ["CNG bus", "Keke"], default=["CNG bus", "Keke"],
    help="Applies to wait samples (type used) and vehicle trips.",
)
hour_range = st.sidebar.slider("Hour of day", 6, 21, (6, 21))


def apply_filters(frame: pd.DataFrame, type_col: str | None = None) -> pd.DataFrame:
    mask = (
        frame["Date"].dt.date.between(d_from, d_to)
        & frame["Day"].isin(days)
        & frame["Block"].isin(blocks)
        & frame["stop_direction"].isin(sel_routes)
        & frame["hour"].between(hour_range[0], hour_range[1] + 0.999)
    )
    if type_col and type_col in frame:
        mask &= frame[type_col].isin(types)
    return frame.loc[mask.fillna(False)]


queue = apply_filters(queue_all)
wait = apply_filters(wait_all, "Type used")
vehicle = apply_filters(vehicle_all, "Type")
completed = wait.loc[wait["wait_event"]]

st.sidebar.divider()
st.sidebar.caption(
    f"**In view:** {len(queue):,} queue snapshots · {len(wait):,} wait samples · "
    f"{len(vehicle):,} vehicle arrivals"
)

# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
st.title("OAU Campus Transport Dashboard")
st.caption(
    "Queues, waiting times and vehicle capacity at campus CNG bus and Keke stops, "
    f"{dmin:%d %b} – {dmax:%d %b %Y}, plus the student survey."
)

if wait.empty and queue.empty and vehicle.empty:
    st.warning("No observations match the current filters. Widen the sidebar selections.")
    st.stop()

tabs = st.tabs([
    "📊 Overview", "⏱️ Waiting times", "👥 Queues & demand",
    "🚐 Vehicles & capacity", "🧪 Statistical tests", "📝 Survey", "🗂️ Data",
])

# ==========================================================================
# Overview
# ==========================================================================
with tabs[0]:
    veh = vehicle.copy()
    cap = pd.to_numeric(veh["Capacity"], errors="coerce").fillna(
        veh["Type"].map(CAPACITIES)
    )
    boarded = pd.to_numeric(veh["Boarded"], errors="coerce")
    left = pd.to_numeric(veh["Left behind"], errors="coerce")
    within10 = completed["wait_minutes"].le(10).mean() if len(completed) else np.nan

    c = st.columns(6)
    c[0].metric("Completed waits", f"{len(completed):,}",
                help=f"{int(wait['censored'].sum()):,} unfinished / censored samples excluded")
    c[1].metric("Median wait", f"{completed['wait_minutes'].median():.1f} min" if len(completed) else "—")
    c[2].metric("90th pct wait", f"{completed['wait_minutes'].quantile(.9):.0f} min" if len(completed) else "—")
    c[3].metric("Boarded ≤ 10 min", f"{within10:.0%}" if pd.notna(within10) else "—")
    c[4].metric("Mean load factor", f"{(boarded / cap).mean():.0%}" if len(veh) else "—")
    lb_rate = left.sum() / (boarded.sum() + left.sum()) if len(veh) else np.nan
    c[5].metric("Left-behind rate", f"{lb_rate:.0%}" if pd.notna(lb_rate) else "—",
                help="Passengers left behind ÷ (boarded + left behind)")

    st.write("")
    left_col, right_col = st.columns(2)
    with left_col:
        if len(completed):
            g = (
                completed.groupby("stop_direction")["wait_minutes"]
                .agg(mean="mean", median="median", p90=lambda s: s.quantile(.9), n="count")
                .reset_index().sort_values("mean")
            )
            fig = go.Figure()
            fig.add_bar(y=g["stop_direction"], x=g["mean"], orientation="h",
                        name="Mean", marker_color="#1f6f78",
                        customdata=g[["median", "p90", "n"]],
                        hovertemplate="%{y}<br>Mean %{x:.1f} min<br>Median %{customdata[0]:.0f}"
                                      "<br>P90 %{customdata[1]:.0f}<br>n=%{customdata[2]}<extra></extra>")
            fig.add_scatter(y=g["stop_direction"], x=g["p90"], mode="markers",
                            name="90th percentile",
                            marker=dict(symbol="line-ns-open", size=16, color="#d9534f", line_width=3))
            fig.update_xaxes(title="minutes")
            st.plotly_chart(style(fig, 460, "Waiting time by stop → direction"), width="stretch")
    with right_col:
        if len(queue):
            q = (
                queue.groupby("hour_slot")
                .agg(mean_queue=("Queue size", "mean"), arrivals=("New arrivals (10 min)", "mean"))
                .reset_index()
            )
            fig = go.Figure()
            fig.add_bar(x=q["hour_slot"], y=q["arrivals"] * 6, name="Arrivals / hour",
                        marker_color="rgba(224,161,0,0.55)")
            fig.add_scatter(x=q["hour_slot"], y=q["mean_queue"], name="Mean queue",
                            mode="lines+markers", line=dict(color="#1f6f78", width=3))
            fig.update_xaxes(title="hour of day", dtick=1, tickformat="02d")
            fig.update_yaxes(title="people")
            st.plotly_chart(style(fig, 460, "Daily rhythm: queue length and arrivals"),
                            width="stretch")

    findings = HERE / "FINDINGS.md"
    if findings.exists():
        text = findings.read_text(encoding="utf-8")
        key = text.split("## Key findings", 1)[-1].split("\n## ", 1)[0]
        with st.expander("Key findings from the full-dataset analysis (FINDINGS.md)", expanded=True):
            st.markdown(key)

# ==========================================================================
# Waiting times
# ==========================================================================
with tabs[1]:
    if completed.empty:
        st.info("No completed waits in the current selection.")
    else:
        a, b = st.columns([1, 1])
        with a:
            fig = px.histogram(
                completed, x="wait_minutes", color="Type used", nbins=45,
                barmode="overlay", opacity=0.7, color_discrete_map=TYPE_COLORS,
                labels={"wait_minutes": "wait (minutes)", "Type used": "Type"},
            )
            st.plotly_chart(style(fig, 400, "Distribution of completed waits"), width="stretch")
        with b:
            fig = px.ecdf(
                completed, x="wait_minutes", color="Type used",
                color_discrete_map=TYPE_COLORS,
                labels={"wait_minutes": "wait (minutes)", "Type used": "Type"},
            )
            for t in (5, 10, 15):
                fig.add_vline(x=t, line_dash="dot", line_color="grey",
                              annotation_text=f"{t} min", annotation_position="bottom right")
            fig.update_yaxes(title="share boarded", tickformat=".0%")
            st.plotly_chart(style(fig, 400, "Cumulative share boarded by wait time"),
                            width="stretch")

        st.subheader("Probability of boarding within a threshold")
        thr = st.slider("Threshold (minutes)", 1, 30, 10, key="thr")
        rows = []
        for route, grp in completed.groupby("stop_direction"):
            n = len(grp)
            k = int(grp["wait_minutes"].le(thr).sum())
            lo, hi = wilson_interval(k, n)
            rows.append({"stop_direction": route, "share": k / n, "lo": lo, "hi": hi, "n": n})
        bp = pd.DataFrame(rows).sort_values("share")
        fig = go.Figure(go.Bar(
            y=bp["stop_direction"], x=bp["share"], orientation="h",
            marker=dict(color=bp["share"], colorscale="RdYlGn", cmin=0.3, cmax=1),
            error_x=dict(type="data", symmetric=False,
                         array=bp["hi"] - bp["share"], arrayminus=bp["share"] - bp["lo"],
                         color="#555"),
            customdata=bp[["n", "lo", "hi"]],
            hovertemplate="%{y}<br>%{x:.1%} (95% CI %{customdata[1]:.1%}–%{customdata[2]:.1%})"
                          "<br>n=%{customdata[0]}<extra></extra>",
        ))
        fig.update_xaxes(tickformat=".0%", range=[0, 1.02], title=f"share boarded within {thr} min")
        st.plotly_chart(style(fig, 460, f"Boarded within {thr} minutes (Wilson 95% CI, completed cases)"),
                        width="stretch")

        a, b = st.columns(2)
        with a:
            fig = px.box(
                completed, x="Block", y="wait_minutes", color="Block",
                category_orders={"Block": ["AM", "MD", "PM"]},
                color_discrete_map=BLOCK_COLORS, points=False,
                labels={"wait_minutes": "wait (minutes)"},
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(style(fig, 380, "Wait by time block"), width="stretch")
        with b:
            hr = (
                completed.groupby(["hour_slot", "Type used"])["wait_minutes"]
                .median().reset_index()
            )
            fig = px.line(hr, x="hour_slot", y="wait_minutes", color="Type used",
                          markers=True, color_discrete_map=TYPE_COLORS,
                          labels={"hour_slot": "hour joined", "wait_minutes": "median wait (min)",
                                  "Type used": "Type"})
            fig.update_xaxes(dtick=1)
            st.plotly_chart(style(fig, 380, "Median wait by hour joined"), width="stretch")

        st.subheader("Summary by stop → direction and block")
        summary = (
            completed.groupby(["stop_direction", "Block"])["wait_minutes"]
            .agg(n="count", mean="mean", median="median",
                 p90=lambda s: s.quantile(.9), max="max")
            .reset_index().sort_values("mean", ascending=False)
        )
        st.dataframe(
            summary, hide_index=True, width="stretch",
            column_config={
                "stop_direction": "Stop → direction",
                "mean": st.column_config.ProgressColumn(
                    "Mean (min)", format="%.1f", min_value=0,
                    max_value=float(summary["mean"].max() or 1)),
                "median": st.column_config.NumberColumn("Median", format="%.1f"),
                "p90": st.column_config.NumberColumn("P90", format="%.1f"),
                "max": st.column_config.NumberColumn("Max", format="%.0f"),
            },
        )

# ==========================================================================
# Queues & demand
# ==========================================================================
with tabs[2]:
    if queue.empty:
        st.info("No queue snapshots in the current selection.")
    else:
        per_hour = (
            queue.groupby(["stop_direction", "hour_slot"])
            .agg(mean_queue=("Queue size", "mean"), max_queue=("Queue size", "max"),
                 arrivals_10=("New arrivals (10 min)", "mean"), n=("Queue size", "count"))
            .reset_index()
        )
        peaks = per_hour.loc[per_hour.groupby("stop_direction")["mean_queue"].idxmax()]
        peaks = peaks.sort_values("mean_queue", ascending=False)
        top = peaks.head(4)
        cols = st.columns(len(top))
        for col, (_, r) in zip(cols, top.iterrows()):
            col.metric(r["stop_direction"], f"{r['mean_queue']:.0f} people",
                       f"peak at {hour_label(r['hour_slot'])}", delta_color="off")

        heat = per_hour.pivot(index="stop_direction", columns="hour_slot", values="mean_queue")
        heat = heat.loc[peaks["stop_direction"]]
        fig = px.imshow(
            heat, aspect="auto", color_continuous_scale=SEQ_SCALE,
            labels=dict(x="hour of day", y="", color="mean queue"),
            text_auto=".0f",
        )
        fig.update_xaxes(dtick=1)
        st.plotly_chart(style(fig, 480, "Mean queue size — stop → direction × hour"),
                        width="stretch")

        a, b = st.columns(2)
        with a:
            focus = st.multiselect(
                "Routes to compare", peaks["stop_direction"].tolist(),
                default=peaks["stop_direction"].head(4).tolist(), key="qroutes",
            )
            fig = px.line(
                per_hour[per_hour["stop_direction"].isin(focus)],
                x="hour_slot", y="mean_queue", color="stop_direction", markers=True,
                labels={"hour_slot": "hour", "mean_queue": "mean queue (people)",
                        "stop_direction": ""},
            )
            fig.update_xaxes(dtick=1)
            st.plotly_chart(style(fig, 420, "Rush profile by route"), width="stretch")
        with b:
            st.write("")
            st.write("")
            st.write("")
            hourly = (
                queue.groupby(["Date", "Day", "is_weekend", "stop_direction", "hour_slot"])
                ["New arrivals (10 min)"].sum().reset_index(name="arrivals_per_hour")
            )
            hourly["Day type"] = np.where(hourly["is_weekend"], "Weekend", "Weekday")
            agg = hourly.groupby(["Day type", "hour_slot"])["arrivals_per_hour"].mean().reset_index()
            fig = px.line(agg, x="hour_slot", y="arrivals_per_hour", color="Day type",
                          markers=True,
                          color_discrete_map={"Weekday": "#1f6f78", "Weekend": "#e0a100"},
                          labels={"hour_slot": "hour", "arrivals_per_hour": "arrivals per route-hour"})
            fig.update_xaxes(dtick=1)
            st.plotly_chart(style(fig, 420, "Passenger arrivals: weekday vs weekend"),
                            width="stretch")

        by_day = (
            queue.groupby("Day")["Queue size"].mean()
            .reindex(DAY_ORDER).dropna().reset_index()
        )
        fig = px.bar(by_day, x="Day", y="Queue size", color="Queue size",
                     color_continuous_scale=SEQ_SCALE, labels={"Queue size": "mean queue"})
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(style(fig, 320, "Mean queue by day of week"), width="stretch")

# ==========================================================================
# Vehicles & capacity
# ==========================================================================
with tabs[3]:
    if vehicle.empty:
        st.info("No vehicle observations in the current selection.")
    else:
        headway, load, dc = vehicle_efficiency(queue, vehicle)
        load = load.dropna(subset=["Type"])

        counts = vehicle.groupby("Type").size()
        c = st.columns(4)
        c[0].metric("Vehicle arrivals", f"{len(vehicle):,}")
        c[1].metric("CNG bus / Keke", f"{counts.get('CNG bus', 0):,} / {counts.get('Keke', 0):,}")
        c[2].metric("Distinct vehicle IDs", f"{vehicle['Vehicle ID'].nunique():,}")
        c[3].metric("Median headway",
                    f"{headway['median_headway_min'].median():.1f} min" if len(headway) else "—")

        a, b = st.columns(2)
        with a:
            fig = px.bar(
                load.sort_values("load_factor_pct"), y="stop_direction", x="load_factor_pct",
                color="Type", barmode="group", orientation="h",
                color_discrete_map=TYPE_COLORS,
                labels={"load_factor_pct": "mean load factor (%)", "stop_direction": ""},
            )
            fig.add_vline(x=100, line_dash="dot", line_color="#d9534f")
            st.plotly_chart(style(fig, 480, "Load factor by route and vehicle type"),
                            width="stretch")
        with b:
            fig = px.bar(
                load.sort_values("left_behind_rate"), y="stop_direction", x="left_behind_rate",
                color="Type", barmode="group", orientation="h",
                color_discrete_map=TYPE_COLORS,
                labels={"left_behind_rate": "share of passengers left behind", "stop_direction": ""},
            )
            fig.update_xaxes(tickformat=".0%")
            st.plotly_chart(style(fig, 480, "Left-behind rate by route and vehicle type"),
                            width="stretch")

        hw = headway.dropna(subset=["median_headway_min"])
        hw_heat = hw.pivot(index="stop_direction", columns="hour_slot", values="median_headway_min")
        fig = px.imshow(hw_heat, aspect="auto", color_continuous_scale="Blues",
                        text_auto=".0f",
                        labels=dict(x="hour of day", y="", color="median headway (min)"))
        fig.update_xaxes(dtick=1)
        st.plotly_chart(style(fig, 440, "Median headway between vehicle arrivals (min)"),
                        width="stretch")

        dc = dc.dropna(subset=["demand_to_capacity_ratio"])
        if len(dc):
            dc_heat = dc.pivot(index="stop_direction", columns="hour_slot",
                               values="demand_to_capacity_ratio")
            fig = px.imshow(dc_heat, aspect="auto", color_continuous_scale="RdYlGn_r",
                            zmin=0, zmax=2, text_auto=".1f",
                            labels=dict(x="hour of day", y="", color="demand ÷ seats"))
            fig.update_xaxes(dtick=1)
            st.plotly_chart(style(fig, 440, "Demand-to-capacity ratio (>1 means more passengers than seats leaving)"),
                            width="stretch")

        if True:
            st.caption("ℹ️ The fleet-availability sheet (D) has no records yet, so fleet charts are omitted.")

# ==========================================================================
# Statistical tests (full dataset, from outputs/tables)
# ==========================================================================
with tabs[4]:
    st.caption("These results come from the full-dataset analysis and do not react to the sidebar filters.")
    tests = load_table("hypothesis_tests.csv")
    if tests.empty:
        st.info("Upload hypothesis_tests.csv next to app.py.")
    else:
        t = tests.copy()
        t["label"] = t["question"] + " · " + t["test_name"]
        t["significant"] = t["p_value"].lt(0.05)
        f = t.dropna(subset=["effect_size"]).iloc[::-1]
        fig = go.Figure()
        fig.add_scatter(
            x=f["effect_size"], y=f["label"], mode="markers",
            marker=dict(size=12, color=np.where(f["significant"], "#1f6f78", "#aaaaaa")),
            error_x=dict(type="data", symmetric=False,
                         array=(f["effect_size_ci95_high"] - f["effect_size"]).fillna(0),
                         arrayminus=(f["effect_size"] - f["effect_size_ci95_low"]).fillna(0)),
            customdata=f[["effect_size_name", "p_value", "n_group_1", "n_group_2"]],
            hovertemplate="%{y}<br>%{customdata[0]} = %{x:.3f}<br>p = %{customdata[1]:.2g}"
                          "<br>n = %{customdata[2]} / %{customdata[3]}<extra></extra>",
        )
        fig.add_vline(x=0, line_color="grey")
        fig.update_xaxes(title="effect size (95% CI)")
        st.plotly_chart(style(fig, 460, "Effect sizes across hypothesis tests"),
                        width="stretch")

        st.dataframe(
            t[["question", "test", "test_name", "groups", "n_group_1", "n_group_2",
               "statistic", "p_value", "effect_size", "effect_size_name", "decision_at_0_05"]],
            hide_index=True, width="stretch",
            column_config={
                "p_value": st.column_config.NumberColumn("p-value", format="%.2e"),
                "effect_size": st.column_config.NumberColumn("Effect", format="%.3f"),
                "statistic": st.column_config.NumberColumn(format="%.1f"),
            },
        )
        with st.expander("Interpretation notes"):
            for _, r in t.iterrows():
                st.markdown(f"**{r['question']} – {r['test_name']}:** {r['interpretation']}")

    sp = load_table("spearman_correlations.csv")
    if not sp.empty:
        sp = sp.set_index("variable")
        fig = px.imshow(sp, text_auto=".2f", color_continuous_scale="RdBu_r",
                        zmin=-1, zmax=1, aspect="auto")
        st.plotly_chart(style(fig, 420, "Spearman correlations between operating metrics"),
                        width="stretch")

# ==========================================================================
# Survey
# ==========================================================================
with tabs[5]:
    survey = load_survey()
    if survey.empty:
        st.info("Upload survey_clean.csv next to app.py.")
    else:
        c = st.columns(4)
        c[0].metric("Respondents", f"{len(survey):,}")
        c[1].metric("Typical wait (reported, midpoint)",
                    f"{survey['wait_min_mid'].mean():.1f} min")
        often = survey["failed_boarding"].isin(["Often", "Always"]).mean()
        c[2].metric("Often/always can't board first vehicle", f"{often:.0%}")
        c[3].metric("Would use a tracking app",
                    f"{survey['tracking_app'].eq('Yes').mean():.0%}")

        ORDERS = {
            "typical_wait": ["0 to 5 minutes", "6 to 10 minutes", "11 to 15 minutes",
                             "16 to 30 minutes", "More than 30 minutes"],
            "longest_wait": ["0 to 5 minutes", "6 to 15 minutes", "16 to 30 minutes",
                             "31 to 60 minutes", "More than 60 minutes"],
            "failed_boarding": ["Never", "Rarely", "Sometimes", "Often", "Always"],
            "walking_time": ["Less than 1 minute", "1 to 5 minutes", "6 to 10 minutes",
                             "More than 10 minutes"],
            "fare_affordability": ["Very affordable", "Somewhat affordable",
                                   "Neither affordable nor expensive", "Somewhat expensive",
                                   "Very expensive"],
            "safety": ["Very unsafe", "Unsafe", "Neutral", "Safe", "Very safe"],
            "comfort": ["Very uncomfortable", "Uncomfortable", "Neutral", "Comfortable",
                        "Very comfortable"],
            "usage_frequency": ["Daily", "Several times a week", "Once a week", "Occasionally"],
        }
        QUESTIONS = {
            "typical_wait": "Typical wait before boarding",
            "longest_wait": "Longest wait experienced",
            "failed_boarding": "Unable to board first vehicle (full)",
            "walking_time": "Walk to nearest stop",
            "fare_affordability": "Fare affordability",
            "safety": "Perceived safety",
            "comfort": "Comfort",
            "tracking_app": "Would use a tracking app",
            "transport_used": "Transport type used",
            "transport_preference": "Preferred transport type",
            "usage_frequency": "How often they use campus transport",
            "boarding_stop": "Usual boarding stop",
            "destination": "Usual destination",
            "travel_purpose": "Main reason for travel",
            "directness": "Goes directly to destination",
        }
        a, b = st.columns([1, 1])
        with a:
            q = st.selectbox("Question", list(QUESTIONS), format_func=QUESTIONS.get)
            split = st.selectbox(
                "Break down by", ["(none)", "transport_used", "transport_preference",
                                  "usage_frequency", "boarding_stop"],
                format_func=lambda k: QUESTIONS.get(k, k),
            )
            d = survey.dropna(subset=[q])
            order = ORDERS.get(q) or d[q].value_counts().index.tolist()
            if split == "(none)":
                vc = d[q].value_counts().reindex(order).dropna().reset_index()
                vc.columns = [q, "count"]
                vc["share"] = vc["count"] / vc["count"].sum()
                fig = px.bar(vc, x="count", y=q, orientation="h", text=vc["share"].map("{:.0%}".format),
                             color_discrete_sequence=["#1f6f78"], labels={q: ""})
            else:
                ct = d.groupby([q, split]).size().reset_index(name="count")
                fig = px.bar(ct, x="count", y=q, color=split, orientation="h",
                             category_orders={q: order}, labels={q: "", split: QUESTIONS.get(split, split)})
            fig.update_yaxes(categoryorder="array", categoryarray=order[::-1])
            st.plotly_chart(style(fig, 420, QUESTIONS[q]), width="stretch")
        with b:
            for col_name, title in (("preference_reasons", "Why they prefer their transport type"),
                                    ("desired_improvements", "Improvements students want")):
                exploded = (
                    survey[col_name].dropna().str.split(r",\s*").explode().str.strip()
                )
                vc = exploded[exploded.ne("")].value_counts().head(8).reset_index()
                vc.columns = ["option", "count"]
                fig = px.bar(vc.iloc[::-1], x="count", y="option", orientation="h",
                             color_discrete_sequence=["#e0a100"], labels={"option": ""})
                fig.update_yaxes(dtick=1, automargin=True)
                st.plotly_chart(style(fig, 320, title), width="stretch")

        comp = load_table("survey_observed_wait_comparison.csv")
        if not comp.empty:
            comp = comp.dropna(subset=["observed_wait_mean_min"])
            fig = go.Figure()
            fig.add_bar(x=comp["boarding_stop"], y=comp["reported_wait_mean_min"],
                        name="Reported (survey)", marker_color="#e0a100",
                        customdata=comp["reported_wait_n"],
                        hovertemplate="%{x}: %{y:.1f} min (n=%{customdata})<extra></extra>")
            fig.add_bar(x=comp["boarding_stop"], y=comp["observed_wait_mean_min"],
                        name="Observed (field)", marker_color="#1f6f78",
                        customdata=comp["observed_wait_n"],
                        hovertemplate="%{x}: %{y:.1f} min (n=%{customdata:,})<extra></extra>")
            fig.update_yaxes(title="mean wait (min)")
            st.plotly_chart(style(fig, 380, "Perceived vs observed waiting time by boarding stop"),
                            width="stretch")
            st.caption("Survey midpoints exclude open-ended categories; observed waits are completed B2 samples.")

        comments = survey["other_comments"].dropna()
        comments = comments[comments.str.len() > 3]
        if len(comments):
            with st.expander(f"Student comments ({len(comments)})"):
                for text in comments:
                    st.markdown(f"> {text}")

# ==========================================================================
# Data explorer
# ==========================================================================
with tabs[6]:
    choice = st.radio(
        "Dataset", ["Wait samples (B2)", "Queue snapshots (B1)", "Vehicle trips (C)"],
        horizontal=True,
    )
    df = {"Wait samples (B2)": wait, "Queue snapshots (B1)": queue,
          "Vehicle trips (C)": vehicle}[choice]
    drop = [c for c in df.columns if c.endswith(" minutes") or c in
            ("Date_original", "time_of_day", "date_day_mismatch", "is_weekend")]
    view = df.drop(columns=drop)
    st.caption(f"{len(view):,} rows after filters")
    st.dataframe(view, width="stretch", height=520, hide_index=True)
    st.download_button(
        "⬇️ Download filtered CSV", view.to_csv(index=False).encode("utf-8"),
        file_name=f"{choice.split('(')[1].strip(')')}_filtered.csv", mime="text/csv",
    )
