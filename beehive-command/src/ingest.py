from datetime import date, timedelta

import pandas as pd

EXCEL_EPOCH = date(1899, 12, 30)

# pandas/openpyxl auto-converts Excel dates to pd.Timestamp when it can.
# For any remaining raw serial integers, fall back to the EXCEL_EPOCH formula.

_DATE_COLS = {
    "inspections": ["Date"],
    "mites": ["Sample Date", "Treatment Date", "Retest Date"],
    "splits": ["Date"],
    "mating_nucs": ["Install Date", "Expected Emergence", "First Egg Check"],
    "queen_assignment": ["Install Date", "Expected Emergence", "First Egg Check"],
    "larvae_calendar": ["Transfer Date", "Next Date", "Start Date", "End Date"],
    "batch_tracker": [
        "Day 0", "Egg Check (Day 2)", "Larvae Ready", "Move Cups",
        "Cells Capped", "Split Cells", "Emergence", "Egg Check (New Queens)",
    ],
    "honey_harvest": ["Date"],
}

_SHEET_MAP = {
    "inspections":      ("Inspections",              1),
    "mites":            ("Mite & Treatment",          1),
    "splits":           ("Splits & Captures",         1),
    "mating_nucs":      ("Mating Nucs",               1),
    "queen_assignment": ("Queen Assignment",          1),
    "larvae_calendar":  ("Larvae Transfer Calendar",  1),
    "batch_tracker":    ("Batch Tracker",             1),
    "lists":            ("Lists",                     0),
    "honey_harvest":    ("Honey Harvest Log",         2),
}


def xl_date(val) -> date | None:
    """Normalize any date-like value to a Python date."""
    if val is None:
        return None
    # pandas Timestamp (most common — openpyxl auto-converts)
    if hasattr(val, "date"):
        try:
            return val.date()
        except Exception:
            return None
    # Already a plain Python date
    if isinstance(val, date):
        return val
    # Raw Excel serial integer
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(val, (int, float)):
        return EXCEL_EPOCH + timedelta(days=int(val))
    return None


def _convert_dates(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for col in cols:
        if col in df.columns:
            df[col] = df[col].apply(xl_date)
    return df


def load_workbook(path: str) -> dict[str, pd.DataFrame]:
    tables: dict[str, pd.DataFrame] = {}
    for key, (sheet_name, header_row) in _SHEET_MAP.items():
        df = pd.read_excel(path, sheet_name=sheet_name, header=header_row, engine="openpyxl")
        df.dropna(how="all", inplace=True)
        df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]
        df.reset_index(drop=True, inplace=True)
        if key in _DATE_COLS:
            df = _convert_dates(df, _DATE_COLS[key])
        tables[key] = df
    return tables
