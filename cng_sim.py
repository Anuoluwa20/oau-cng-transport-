"""Queue simulation and survival analysis for the OAU campus transport study.

The simulator replays each route-day from the field logs:
  * passengers arrive as recorded in sheet B1 (new arrivals per 10 minutes,
    spread evenly across each 10-minute window; the 08:00 queue is present at 08:00);
  * vehicles arrive as recorded in sheet C, each taking up to its
    "spaces free on arrival" from the front of the queue (first come, first served).
Each simulated passenger's wait = arrival time of the vehicle they board − their
arrival time. Passengers still queuing at 18:00 are censored at 18:00.

Because it reproduces the waits timed in sheet B2 (see `calibration`), it can be
used to ask "what if": what happens to the 90th-percentile wait if vehicles are
spaced evenly, added at peak hours, or moved from quiet routes.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

END_OF_DAY = 18 * 60.0
PCTS = (50, 75, 90, 95)


# ---------------------------------------------------------------------------
# Survival analysis (Kaplan–Meier) with unfinished waits censored at 18:00
# ---------------------------------------------------------------------------
def survival_input(wait: pd.DataFrame) -> pd.DataFrame:
    """Durations and event flags: completed waits are events; unfinished ones are
    censored at the end of observation (18:00) — their wait was at least that long."""
    w = wait.copy()
    dur = w["wait_minutes"].copy()
    cens = w["censored"] & w["joined_minutes"].notna()
    dur[cens] = (END_OF_DAY - w.loc[cens, "joined_minutes"]).clip(lower=0)
    w["duration"] = dur
    w["event"] = ~w["censored"]
    return w.dropna(subset=["duration"])


def kaplan_meier(duration: pd.Series, event: pd.Series) -> pd.DataFrame:
    """Return the share still waiting S(t) at each minute t."""
    d = pd.DataFrame({"t": np.round(duration.values.astype(float)), "e": event.values.astype(bool)})
    times = np.arange(0, int(np.ceil(d["t"].max())) + 1)
    n_at_risk = len(d)
    s = 1.0
    out = []
    grouped = d.groupby("t")
    events = grouped["e"].sum()
    totals = grouped.size()
    for t in times:
        out.append((t, s))  # S just before leaving time t is S(t-)
        if t in totals.index:
            e = events.get(t, 0)
            if n_at_risk > 0:
                s *= 1 - e / n_at_risk
            n_at_risk -= totals[t]
    surv = pd.DataFrame(out, columns=["t", "still_waiting"])
    # S(t) after events at t
    surv["still_waiting"] = surv["still_waiting"].shift(-1).fillna(s)
    return surv


def km_percentile(surv: pd.DataFrame, p: float) -> float:
    """Smallest t with S(t) <= 1 - p/100 (the p-th percentile wait)."""
    hit = surv.loc[surv["still_waiting"] <= 1 - p / 100, "t"]
    return float(hit.iloc[0]) if len(hit) else np.nan


def area_under_curve(surv: pd.DataFrame) -> float:
    """Area under S(t) = (restricted) mean wait in minutes."""
    return float(surv["still_waiting"].sum())


def percentile_table(wait: pd.DataFrame, by: list[str] | None = None) -> pd.DataFrame:
    """P50/P75/P90/P95 and area under the curve, KM-adjusted for unfinished waits."""
    w = survival_input(wait)
    groups = [((), w)] if not by else w.groupby(by)
    rows = []
    for key, g in groups:
        surv = kaplan_meier(g["duration"], g["event"])
        row = dict(zip(by or [], key if isinstance(key, tuple) else (key,)))
        row.update({f"P{p}": km_percentile(surv, p) for p in PCTS})
        row["area"] = area_under_curve(surv)
        row["n"] = len(g)
        row["unfinished"] = int((~g["event"]).sum())
        row["over15"] = float(surv.loc[surv["t"] == 15, "still_waiting"].iat[0]) if (surv["t"] == 15).any() else 0.0
        rows.append(row)
    return pd.DataFrame(rows)


def tail_share(waits: pd.Series, p: float = 90) -> float:
    """Share of all passenger-minutes spent by the passengers above the p-th percentile."""
    w = waits.dropna()
    cut = np.percentile(w, p)
    return float(w[w > cut].sum() / w.sum()) if w.sum() else np.nan


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def _arrivals(qd: pd.DataFrame) -> np.ndarray:
    """Passenger arrival times (minutes) for one route-day from sheet B1.

    Each count is "new arrivals in the last 10 minutes". When two counts were taken
    less than 10 minutes apart the windows overlap, so only the new part of the
    window (gap / 10 of the count) is added, to avoid counting people twice."""
    qd = qd.dropna(subset=["Time minutes"]).sort_values("Time minutes")
    times: list[float] = []
    prev = None
    for t, new, queue in zip(qd["Time minutes"], qd["New arrivals (10 min)"], qd["Queue size"]):
        if prev is None:  # people already queuing when observation began
            times += [t] * int(max(queue, 0))
            prev = t
            continue
        gap = t - prev
        if gap <= 0:
            continue
        span = min(gap, 10.0)
        n = int(round(max(new, 0) * span / 10.0))
        if n:
            times += list(t - span + (np.arange(n) + 0.5) * span / n)
        prev = t
    return np.sort(np.array(times, dtype=float))


def _vehicles(vd: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    vd = vd.dropna(subset=["Arrived minutes"]).sort_values("Arrived minutes")
    cap = pd.to_numeric(vd["Spaces free on arrival"], errors="coerce")
    full_cap = pd.to_numeric(vd["Capacity"], errors="coerce").fillna(vd["Type"].map({"CNG bus": 13, "Keke": 5}))
    cap = cap.fillna(full_cap)
    arr = vd["Arrived minutes"].to_numpy(float)
    dep = pd.to_numeric(vd["Departed minutes"], errors="coerce").to_numpy(float)
    dep = np.where(np.isnan(dep) | (dep < arr), arr, dep)
    return arr, dep, cap.to_numpy(float), vd["Type"].astype(str).to_numpy()


def serve(arr: np.ndarray, veh_t: np.ndarray, veh_cap: np.ndarray, veh_dep: np.ndarray | None = None) -> np.ndarray:
    """FIFO boarding. A vehicle loads everyone already queuing when it arrives and
    anyone who walks up while it is still at the stop (until it departs), up to its
    free seats. Returns each passenger's wait (NaN = still waiting at 18:00)."""
    if veh_dep is None:
        veh_dep = veh_t
    order = np.argsort(veh_t)
    veh_t, veh_cap, veh_dep = veh_t[order], veh_cap[order], veh_dep[order]
    waits = np.full(len(arr), np.nan)
    head = 0
    for t, c, d in zip(veh_t, veh_cap, veh_dep):
        avail_end = np.searchsorted(arr, max(d, t), side="right")
        take = int(min(c, max(avail_end - head, 0)))
        if take:
            waits[head:head + take] = np.maximum(t - arr[head:head + take], 0)
            head += take
    return waits


def simulate(queue: pd.DataFrame, vehicle: pd.DataFrame, modify=None) -> pd.DataFrame:
    """Simulate every route-day. `modify(route, date, veh_t, veh_cap, veh_type)` may
    return altered (veh_t, veh_cap) to test a scenario."""
    out = []
    vgroups = {k: g for k, g in vehicle.groupby(["Date", "stop_direction"])}
    for (date, route), qd in queue.groupby(["Date", "stop_direction"]):
        arr = _arrivals(qd)
        if not len(arr):
            continue
        vd = vgroups.get((date, route))
        if vd is None:
            vt, vdep, vc, vty = (np.array([]),) * 4
        else:
            vt, vdep, vc, vty = _vehicles(vd)
        dwell = np.median(vdep - vt) if len(vt) else 0.0
        if modify is not None:
            n0 = len(vt)
            keep_dwell = dict(zip(vt, vdep - vt))
            vt, vc = modify(route, date, vt, vc, vty)
            # moved vehicles keep their dwell time; added ones get the route's median dwell
            vdep = np.array([t + keep_dwell.get(t, dwell) for t in vt])
        wt = serve(arr, vt, vc, vdep)
        out.append(pd.DataFrame({"Date": date, "stop_direction": route, "joined_minutes": arr, "sim_wait": wt}))
    sim = pd.concat(out, ignore_index=True)
    sim["hour_slot"] = np.floor(sim["joined_minutes"] / 60)
    sim["Block"] = np.select([sim["hour_slot"] < 11, sim["hour_slot"] < 15], ["AM", "MD"], "PM")
    sim["censored"] = sim["sim_wait"].isna()
    sim["wait_minutes"] = sim["sim_wait"]
    sim["wait_event"] = ~sim["censored"]
    return sim


def summarize_sim(sim: pd.DataFrame, by: list[str] | None = None) -> pd.DataFrame:
    return percentile_table(sim, by)


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------
def scenario_even_spacing(route, date, vt, vc, vty):
    """Same vehicles each hour, but arriving at evenly spaced times (no bunching)."""
    if not len(vt):
        return vt, vc
    hours = np.floor(vt / 60)
    new_t = vt.copy()
    for h in np.unique(hours):
        m = hours == h
        k = m.sum()
        new_t[m] = h * 60 + (np.arange(k) + 0.5) * 60 / k
    return new_t, vc


def scenario_add_peak(routes_hours: set[tuple[str, int]], extra_per_hour: int = 2, seats: int = 13):
    """Add `extra_per_hour` CNG buses, evenly spaced, in the given (route, hour) cells."""
    def modify(route, date, vt, vc, vty):
        add_t = [h * 60 + (i + 0.5) * 60 / extra_per_hour
                 for (r, h) in routes_hours if r == route for i in range(extra_per_hour)]
        if not add_t:
            return vt, vc
        return np.concatenate([vt, add_t]), np.concatenate([vc, [seats] * len(add_t)])
    return modify


def scenario_reallocate(targets: set[tuple[str, int]], donors: list[str], per_hour: int = 2):
    """Take `per_hour` CNG buses from donor routes in the same hour and run them on target cells."""
    def modify(route, date, vt, vc, vty):
        hours = np.floor(vt / 60) if len(vt) else np.array([])
        if route in donors:
            target_hours = {h for (_, h) in targets}
            keep = np.ones(len(vt), bool)
            for h in target_hours:
                idx = np.where((hours == h) & (vty == "CNG bus"))[0]
                # each target cell needs per_hour buses; spread the donation over donors
                n_take = int(np.ceil(per_hour * sum(1 for (_, hh) in targets if hh == h) / len(donors)))
                keep[idx[:n_take]] = False
            return vt[keep], vc[keep]
        add_t = [h * 60 + (i + 0.5) * 60 / per_hour for (r, h) in targets if r == route for i in range(per_hour)]
        if add_t:
            return np.concatenate([vt, add_t]), np.concatenate([vc, [13] * len(add_t)])
        return vt, vc
    return modify


def compose(*mods):
    """Apply several scenario modifiers in turn."""
    def modify(route, date, vt, vc, vty):
        types = vty
        for m in mods:
            n_before = len(vt)
            vt, vc = m(route, date, vt, vc, types)
            if len(vt) != n_before:  # vehicles were added/removed: treat added ones as buses
                types = np.array(list(types[:min(len(types), len(vt))]) + ["CNG bus"] * max(0, len(vt) - len(types)))
        return vt, vc
    return modify


HOT_CELLS = (
    {("NEW MARKET -> ACADEMICS", h) for h in (8, 9, 10)}
    | {("CAMPUS GATE -> BUS STOP", h) for h in (8, 9, 10)}
    | {("BUS STOP -> CAMPUS GATE", h) for h in (15, 16, 17)}
)
DONORS = ["CAMPUS GATE -> HALL", "HALL -> CAMPUS GATE"]


def scenario_table(queue: pd.DataFrame, vehicle: pd.DataFrame, extra: int = 2) -> tuple[pd.DataFrame, dict]:
    """Run the standard set of what-if scenarios. Returns a summary table and the simulations."""
    days = queue["Date"].nunique()
    runs = {
        "As observed": None,
        "Even spacing (same vehicles)": scenario_even_spacing,
        f"Move {extra} buses/hour from Hall ↔ Campus Gate to the 9 peak route-hours": scenario_reallocate(HOT_CELLS, DONORS, extra),
        f"Add {extra} buses/hour in the 9 peak route-hours": scenario_add_peak(HOT_CELLS, extra),
        f"Move {extra} buses/hour + even spacing": compose(scenario_reallocate(HOT_CELLS, DONORS, extra), scenario_even_spacing),
    }
    sims, rows = {}, []
    for label, mod in runs.items():
        sim = simulate(queue, vehicle, mod)
        sims[label] = sim
        o = percentile_table(sim).iloc[0]
        c = sim[sim["wait_event"]]
        donor = percentile_table(sim[sim["stop_direction"].isin(DONORS)]).iloc[0]
        hot = sim.set_index(["stop_direction", "hour_slot"]).index.isin(list(HOT_CELLS))
        hot_t = percentile_table(sim[hot]).iloc[0]
        rows.append({"scenario": label, "P50": o["P50"], "P75": o["P75"], "P90": o["P90"], "P95": o["P95"],
                     "area": o["area"], "over15": o["over15"],
                     "hours_per_day": c["wait_minutes"].sum() / 60 / days,
                     "peak_P90": hot_t["P90"], "donor_P90": donor["P90"], "donor_area": donor["area"]})
    t = pd.DataFrame(rows)
    base = t.iloc[0]
    t["area_change"] = t["area"] / base["area"] - 1
    t["hours_saved_per_day"] = base["hours_per_day"] - t["hours_per_day"]
    return t, sims
