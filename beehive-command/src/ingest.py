from datetime import date, timedelta

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Google Sheets and Excel share the same serial date epoch.
EXCEL_EPOCH = date(1899, 12, 30)

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
    """Normalize a serial number or date-like value to a Python date.

    Google Sheets returns dates as floats when UNFORMATTED_VALUE is used,
    matching the Excel serial format (epoch = 1899-12-30).
    """
    if val is None or val == "":
        return None
    if hasattr(val, "date"):
        try:
            return val.date()
        except Exception:
            return None
    if isinstance(val, date):
        return val
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(val, (int, float)) and val > 0:
        return EXCEL_EPOCH + timedelta(days=int(val))
    return None


def _convert_dates(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for col in cols:
        if col in df.columns:
            df[col] = df[col].apply(xl_date)
    return df


def _get_client(service_account_json: str) -> gspread.Client:
    creds = Credentials.from_service_account_file(service_account_json, scopes=SCOPES)
    return gspread.authorize(creds)


def _sheet_to_df(spreadsheet: gspread.Spreadsheet, sheet_name: str, header_row: int) -> pd.DataFrame:
    ws = spreadsheet.worksheet(sheet_name)
    # UNFORMATTED_VALUE returns dates as serial floats (same as Excel) and
    # numbers as numbers — avoids locale-dependent date string parsing.
    rows = ws.get(value_render_option="UNFORMATTED_VALUE")
    if len(rows) <= header_row:
        return pd.DataFrame()

    headers = [str(h) for h in rows[header_row]]
    data = rows[header_row + 1:]

    # Pad short rows so every row matches header length
    n = len(headers)
    padded = [row + [""] * (n - len(row)) if len(row) < n else row[:n] for row in data]

    df = pd.DataFrame(padded, columns=headers)
    # Drop columns with no header or auto-generated "Unnamed" names
    df = df.loc[:, [c for c in df.columns if c and not c.startswith("Unnamed")]]
    df.replace("", pd.NA, inplace=True)
    df.dropna(how="all", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def load_workbook(spreadsheet_id: str, service_account_json: str) -> dict[str, pd.DataFrame]:
    client = _get_client(service_account_json)
    spreadsheet = client.open_by_key(spreadsheet_id)
    tables: dict[str, pd.DataFrame] = {}
    for key, (sheet_name, header_row) in _SHEET_MAP.items():
        df = _sheet_to_df(spreadsheet, sheet_name, header_row)
        if key in _DATE_COLS:
            df = _convert_dates(df, _DATE_COLS[key])
        tables[key] = df
    return tables
