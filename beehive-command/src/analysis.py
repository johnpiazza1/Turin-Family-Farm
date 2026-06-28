from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

import pandas as pd


# ---------------------------------------------------------------------------
# HiveState dataclass
# ---------------------------------------------------------------------------

@dataclass
class HiveState:
    hive_id: str
    unit_type: str = ""
    strength: str = ""
    bee_frames: Optional[int] = None
    brood_frames: Optional[int] = None
    queen_status: str = ""
    queen_seen: str = ""
    eggs: str = ""
    larvae: str = ""
    queen_cells: str = ""
    days_since_inspection: Optional[int] = None
    last_inspection_date: Optional[date] = None
    next_action: str = ""
    food_stores: str = ""
    temperament: str = ""
    notes: str = ""
    mite_rate: Optional[float] = None
    mite_pressure: str = ""
    mite_trend: str = ""          # "↑ Rising", "↓ Falling", "→ Stable", or ""
    mite_sample_date: Optional[date] = None
    treatment_status: str = ""
    treatment_type: str = ""
    active_batch_id: str = ""
    larvae_next_critical: str = ""
    larvae_next_date: Optional[date] = None
    mating_nuc_status: str = ""
    honey_ytd_lbs: float = 0.0
    risk_score: int = 0
    alerts: list[str] = field(default_factory=list)
    is_queenless: bool = False
    is_overdue: bool = False
    needs_mite_treatment: bool = False


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------

def get_strength(bee_frames) -> str:
    if bee_frames is None or (isinstance(bee_frames, float) and pd.isna(bee_frames)):
        return "Unknown"
    try:
        frames = float(bee_frames)
    except (ValueError, TypeError):
        return "Unknown"
    if frames >= 8:
        return "Strong"
    if frames >= 5:
        return "Moderate"
    return "Weak"


def classify_mite_rate(rate: float) -> str:
    if rate < 1:
        return "Low"
    if rate < 2:
        return "Moderate"
    if rate < 3:
        return "High"
    return "Critical"


def _is_blank(val: str) -> bool:
    return val.lower() in ("", "nan", "none", "<na>", "n/a", "na")


def _is_yes(val: str) -> bool:
    return val.lower() in ("yes", "y", "true", "1")


def _is_no(val: str) -> bool:
    return val.lower() in ("no", "n", "false", "0")


# ---------------------------------------------------------------------------
# Per-hive lookups against DataFrames
# ---------------------------------------------------------------------------

def days_since_inspection(hive_id: str, inspections: pd.DataFrame) -> tuple[Optional[int], Optional[date]]:
    rows = inspections[inspections["Hive"] == hive_id]
    if rows.empty:
        return None, None
    latest_date = rows["Date"].dropna().max()
    if latest_date is None:
        return None, None
    delta = (date.today() - latest_date).days
    return delta, latest_date


def get_queen_status(hive_id: str, inspections: pd.DataFrame) -> dict:
    rows = inspections[inspections["Hive"] == hive_id].dropna(subset=["Date"])
    if rows.empty:
        return {
            "queen_seen": "", "eggs": "", "larvae": "", "queen_cells": "",
            "status": "No inspections", "is_queenless": False,
        }
    latest = rows.sort_values("Date").iloc[-1]

    queen_seen = str(latest.get("Queen Seen", "")).strip()
    eggs       = str(latest.get("Eggs", "")).strip()
    larvae     = str(latest.get("Larvae", "")).strip()
    cells      = str(latest.get("Queen Cells", "")).strip()

    # All queen fields blank → inspector didn't fill in the queen section
    all_blank = all(_is_blank(v) for v in (queen_seen, eggs, larvae, cells))
    if all_blank:
        status = "Not recorded"
        is_queenless = False
    elif _is_no(queen_seen) and _is_no(eggs) and _is_no(larvae) and _is_blank(cells):
        status = "Queenless"
        is_queenless = True
    elif _is_yes(queen_seen):
        status = "Queen Present"
        is_queenless = False
    elif _is_yes(eggs):
        status = "Eggs Present"
        is_queenless = False
    elif not _is_blank(cells) and not _is_no(cells):
        status = "Queen Cells"
        is_queenless = False
    elif _is_no(queen_seen) and _is_no(eggs):
        status = "Queen Not Seen"
        is_queenless = False
    else:
        status = "Unknown"
        is_queenless = False

    return {
        "queen_seen": queen_seen,
        "eggs": eggs,
        "larvae": larvae,
        "queen_cells": cells,
        "status": status,
        "is_queenless": is_queenless,
    }


def get_mite_pressure(hive_id: str, mites: pd.DataFrame) -> dict:
    rows = mites[mites["Hive ID"] == hive_id].dropna(subset=["Sample Date"])
    if rows.empty:
        return {
            "rate": None, "pressure": "Unknown", "trend": "",
            "sample_date": None, "treatment_status": "", "treatment_type": "",
        }
    sorted_rows = rows.sort_values("Sample Date")
    latest = sorted_rows.iloc[-1]

    def _rate(row) -> Optional[float]:
        try:
            return float(row.get("Mites / 100 Bees"))
        except (ValueError, TypeError):
            return None

    rate = _rate(latest)
    pressure = classify_mite_rate(rate) if rate is not None else "Unknown"

    # Trend: compare last two readings
    trend = ""
    if len(sorted_rows) >= 2:
        prev_rate = _rate(sorted_rows.iloc[-2])
        if rate is not None and prev_rate is not None:
            diff = rate - prev_rate
            if diff > 0.2:
                trend = "↑ Rising"
            elif diff < -0.2:
                trend = "↓ Falling"
            else:
                trend = "→ Stable"

    return {
        "rate": rate,
        "pressure": pressure,
        "trend": trend,
        "sample_date": latest.get("Sample Date"),
        "treatment_status": str(latest.get("Treatment Status", "")).strip(),
        "treatment_type": str(latest.get("Treatment Type", "")).strip(),
    }


def get_next_action(hive_id: str, inspections: pd.DataFrame, larvae_calendar: pd.DataFrame) -> str:
    rows = inspections[inspections["Hive"] == hive_id].dropna(subset=["Date"])
    if not rows.empty:
        latest = rows.sort_values("Date").iloc[-1]
        action = str(latest.get("Next Action", "")).strip()
        if action and action.lower() not in ("nan", "none", ""):
            return action
    lc_rows = larvae_calendar[larvae_calendar.get("Cell Builder Unit", pd.Series(dtype=str)) == hive_id]
    if not lc_rows.empty:
        active = lc_rows[lc_rows.get("Batch Status", pd.Series(dtype=str)).str.lower().isin(["active", "in progress"])]
        if not active.empty:
            critical = str(active.iloc[-1].get("Next Critical", "")).strip()
            if critical and critical.lower() not in ("nan", "none", ""):
                return f"Queen rearing: {critical}"
    return ""


def get_honey_ytd(hive_id: str, honey_harvest: pd.DataFrame) -> float:
    rows = honey_harvest[honey_harvest["Hive"] == hive_id]
    if rows.empty:
        return 0.0
    total = pd.to_numeric(rows["Honey Weight lbs"], errors="coerce").sum()
    return round(float(total), 1)


def get_larvae_activity(hive_id: str, larvae_calendar: pd.DataFrame) -> dict:
    rows = larvae_calendar[
        (larvae_calendar.get("Cell Builder Unit", pd.Series(dtype=str)) == hive_id)
        | (larvae_calendar.get("Active Batch ID", pd.Series(dtype=str)).str.startswith(hive_id, na=False))
    ]
    active = rows[rows.get("Batch Status", pd.Series(dtype=str)).str.lower().str.contains("active|in progress", na=False)]
    if active.empty:
        return {"batch_id": "", "next_critical": "", "next_date": None}
    row = active.sort_values("Next Date").iloc[0] if "Next Date" in active.columns else active.iloc[0]
    return {
        "batch_id": str(row.get("Active Batch ID", "")).strip(),
        "next_critical": str(row.get("Next Critical", "")).strip(),
        "next_date": row.get("Next Date"),
    }


def get_mating_nuc_status(hive_id: str, mating_nucs: pd.DataFrame) -> str:
    rows = mating_nucs[mating_nucs.get("Nuc ID", pd.Series(dtype=str)) == hive_id]
    if rows.empty:
        return ""
    return str(rows.iloc[-1].get("Status", "")).strip()


# ---------------------------------------------------------------------------
# Risk score
# ---------------------------------------------------------------------------

def calculate_risk_score(hs: HiveState) -> int:
    score = 0
    if hs.days_since_inspection is not None:
        score += hs.days_since_inspection * 2
    if hs.is_queenless:
        score += 40
    if hs.strength == "Weak":
        score += 20
    if hs.bee_frames is not None and hs.bee_frames == 0:
        score += 35
    if hs.mite_pressure == "Moderate":
        score += 5
    elif hs.mite_pressure == "High":
        score += 20
    elif hs.mite_pressure == "Critical":
        score += 35
    if hs.mite_trend == "↑ Rising":
        score += 5
    if hs.treatment_status.lower() in ("treat now", "due"):
        score += 25
    if hs.is_overdue:
        score += 30
    if hs.days_since_inspection is not None and hs.days_since_inspection > 7:
        score += 8
    return score


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

def get_alerts(hs: HiveState) -> list[str]:
    alerts = []
    if hs.is_overdue:
        alerts.append("OVERDUE — inspection needed")
    if hs.is_queenless:
        alerts.append("QUEENLESS")
    if hs.queen_status == "Queen Not Seen" and not hs.is_queenless:
        alerts.append("Queen not seen")
    if _is_no(hs.eggs) and hs.queen_status not in ("Not recorded", "Queenless"):
        alerts.append("No eggs seen")
    if not _is_blank(hs.queen_cells) and not _is_no(hs.queen_cells):
        alerts.append(f"Queen cells: {hs.queen_cells}")
    if hs.mite_pressure in ("High", "Critical"):
        alerts.append(f"Mite pressure {hs.mite_pressure}")
    if hs.mite_trend == "↑ Rising" and hs.mite_pressure in ("Moderate", "High", "Critical"):
        alerts.append("Mite rate rising")
    if hs.treatment_status.lower() in ("treat now", "due"):
        alerts.append("Mite treatment due")
    return alerts


# ---------------------------------------------------------------------------
# Active hive registry
# ---------------------------------------------------------------------------

def get_active_hives(lists_df: pd.DataFrame) -> list[str]:
    """Return hive IDs from the HiveID column where Status == Active."""
    if "HiveID" not in lists_df.columns:
        return []

    hives = lists_df["HiveID"].astype(str).str.strip()
    hives = hives[(hives.str.len() > 0) & (hives != "nan")]

    if "Status" in lists_df.columns:
        statuses = lists_df["Status"].astype(str).str.strip().str.lower()
        hives = hives[statuses == "active"]

    return hives.tolist()


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_apiary_state(tables: dict) -> list[HiveState]:
    inspections    = tables["inspections"]
    mites          = tables["mites"]
    larvae_calendar = tables["larvae_calendar"]
    honey_harvest  = tables["honey_harvest"]
    mating_nucs    = tables["mating_nucs"]
    lists_df       = tables["lists"]

    active_hives = get_active_hives(lists_df)
    states = []

    for hive_id in active_hives:
        days, last_date = days_since_inspection(hive_id, inspections)
        queen_info  = get_queen_status(hive_id, inspections)
        mite_info   = get_mite_pressure(hive_id, mites)
        larvae_info = get_larvae_activity(hive_id, larvae_calendar)
        next_action = get_next_action(hive_id, inspections, larvae_calendar)
        honey_ytd   = get_honey_ytd(hive_id, honey_harvest)
        nuc_status  = get_mating_nuc_status(hive_id, mating_nucs)

        bee_frames = None
        food_stores = ""
        temperament = ""
        notes = ""
        rows = inspections[inspections["Hive"] == hive_id].dropna(subset=["Date"])
        if not rows.empty:
            latest = rows.sort_values("Date").iloc[-1]
            try:
                bee_frames = int(float(latest.get("Bee Frames", 0) or 0))
            except (ValueError, TypeError):
                bee_frames = None
            food_stores = str(latest.get("Food Stores", "")).strip()
            temperament = str(latest.get("Temperament", "")).strip()
            notes       = str(latest.get("Notes", "")).strip()

        is_overdue = days is not None and days > 14

        hs = HiveState(
            hive_id=hive_id,
            strength=get_strength(bee_frames),
            bee_frames=bee_frames,
            queen_status=queen_info["status"],
            queen_seen=queen_info["queen_seen"],
            eggs=queen_info["eggs"],
            larvae=queen_info["larvae"],
            queen_cells=queen_info["queen_cells"],
            days_since_inspection=days,
            last_inspection_date=last_date,
            next_action=next_action,
            food_stores=food_stores,
            temperament=temperament,
            notes=notes,
            mite_rate=mite_info["rate"],
            mite_pressure=mite_info["pressure"],
            mite_trend=mite_info["trend"],
            mite_sample_date=mite_info["sample_date"],
            treatment_status=mite_info["treatment_status"],
            treatment_type=mite_info["treatment_type"],
            active_batch_id=larvae_info["batch_id"],
            larvae_next_critical=larvae_info["next_critical"],
            larvae_next_date=larvae_info["next_date"],
            mating_nuc_status=nuc_status,
            honey_ytd_lbs=honey_ytd,
            is_queenless=queen_info["is_queenless"],
            is_overdue=is_overdue,
        )
        hs.risk_score = calculate_risk_score(hs)
        hs.alerts = get_alerts(hs)
        states.append(hs)

    states.sort(key=lambda h: h.risk_score, reverse=True)
    return states
