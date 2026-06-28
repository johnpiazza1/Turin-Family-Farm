"""
Usage:
  python main.py               generate and email the report
  python main.py --dry-run     generate HTML and open in browser (no email)
  python main.py --test-email  send to EMAIL_FROM as a sanity check
"""

import argparse
import sys
import tempfile
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import load_config
from src.ingest import load_workbook
from src.analysis import build_apiary_state
from src.seasonal import get_seasonal_advice
from src.report_builder import build_report
from src.email_sender import send_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Beehive Command — weekly apiary report")
    parser.add_argument("--dry-run", action="store_true", help="Generate HTML and open in browser")
    parser.add_argument("--test-email", action="store_true", help="Send report to EMAIL_FROM")
    args = parser.parse_args()

    config = load_config()
    print(f"Loading spreadsheet: {config.spreadsheet_id}")
    tables = load_workbook(config.spreadsheet_id, config.service_account_json)

    print("Building apiary state...")
    apiary_state = build_apiary_state(tables)
    print(f"  {len(apiary_state)} active hives found")

    seasonal_advice = get_seasonal_advice(apiary_state)
    html = build_report(apiary_state, tables, seasonal_advice, config)

    if args.dry_run:
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
            f.write(html)
            tmp_path = f.name
        print(f"Report written to {tmp_path}")
        webbrowser.open(f"file://{tmp_path}")
        return

    if args.test_email:
        print(f"Test mode: sending to {config.email_from}")
        config.email_to = config.email_from

    send_report(html, config)


if __name__ == "__main__":
    main()
