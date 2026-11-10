"""Data loading and metric helpers for the OAU campus transport dashboard.

Copied from the project's original src/ package (load_data.py, analysis.py) so the
deployed app needs no subfolders. All data files sit next to this file.
"""
from __future__ import annotations

import contextlib
import io
from pathlib import Path

import numpy as np
import pandas as pd

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





def load_frames() -> dict[str, pd.DataFrame]:
    """Load all observation sheets and add the derived fields the app uses."""
    frames = load_all_data()
    wait = prepare_wait_data(frames["wait"])
    for key in ("queue", "vehicle"):
        frames[key]["hour_slot"] = np.floor(frames[key]["hour"])
    wait["hour_slot"] = np.floor(wait["hour"])
    frames["wait"] = wait
    frames["vehicle"]["Type"] = frames["vehicle"]["Type"].astype("string").str.strip()
    for key in ("queue", "wait", "vehicle"):
        f = frames[key]
        f["Day"] = f["Day"].fillna(f["Date"].dt.day_name())
        f["is_weekend"] = f["Day"].isin(["Saturday", "Sunday"])
        for col in ("stop_direction", "Block", "Day", "Stop", "Type", "Type used"):
            if col in f:
                f[col] = f[col].astype(object).where(f[col].notna(), None)
    # The 12 stop-directions on the observation rota (defined by the queue sheet);
    # a handful of stray rows (missing or same-stop destinations) are excluded.
    main_routes = set(frames["queue"]["stop_direction"].dropna()) - {
        r for r in frames["queue"]["stop_direction"].dropna() if "Unknown" in r
    }
    for key in ("queue", "wait", "vehicle"):
        frames[key]["valid_route"] = frames[key]["stop_direction"].isin(main_routes)
    return frames
