from __future__ import annotations

from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .analysis import HiveState

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def _active_batch_rows(tables: dict) -> list[dict]:
    df = tables["batch_tracker"]
    if "Status" not in df.columns:
        return []
    active = df[df["Status"].astype(str).str.lower().str.contains("active|in progress|grafted", na=False)]
    rows = []
    for _, r in active.iterrows():
        row = {k: (v if v is not None and str(v) not in ("nan", "NaT", "None") else "") for k, v in r.items()}
        if "Day 0" in row and hasattr(row["Day 0"], "strftime"):
            row["Day 0"] = row["Day 0"].strftime("%b %d")
        rows.append(row)
    return rows


def _active_larvae_rows(tables: dict) -> list[dict]:
    df = tables["larvae_calendar"]
    if "Batch Status" not in df.columns:
        return []
    active = df[df["Batch Status"].astype(str).str.lower().str.contains("active|in progress", na=False)]
    rows = []
    for _, r in active.iterrows():
        row = {k: (v if v is not None and str(v) not in ("nan", "NaT", "None") else "") for k, v in r.items()}
        for date_col in ("Transfer Date", "Next Date"):
            if date_col in row and hasattr(row[date_col], "strftime"):
                row[date_col] = row[date_col].strftime("%b %d")
        rows.append(row)
    return rows


def build_report(
    apiary_state: list[HiveState],
    tables: dict,
    seasonal_advice: list[str],
    config,
) -> str:
    env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)), autoescape=False)
    template = env.get_template("report.html.j2")

    honey_rows = [h for h in apiary_state if h.honey_ytd_lbs > 0]
    honey_total = sum(h.honey_ytd_lbs for h in apiary_state)

    context = {
        "apiary_name": config.apiary_name,
        "report_date": datetime.now().strftime("%B %d, %Y"),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "excel_path": f"https://docs.google.com/spreadsheets/d/{config.spreadsheet_id}",
        "hive_states": apiary_state,
        "active_hive_count": len(apiary_state),
        "total_bee_frames": sum(h.bee_frames or 0 for h in apiary_state),
        "alert_count": sum(1 for h in apiary_state if h.alerts),
        "seasonal_advice": seasonal_advice,
        "honey_rows": honey_rows,
        "honey_total": honey_total,
        "active_batches": _active_batch_rows(tables),
        "active_larvae": _active_larvae_rows(tables),
        "active_mating_nucs": [h for h in apiary_state if h.mating_nuc_status],
    }
    return template.render(**context)
