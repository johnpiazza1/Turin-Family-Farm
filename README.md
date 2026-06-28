# Turin Family Farm

Personal farm management tools.

## Projects

### `beehive-command/` — Weekly Apiary Report

Automated weekly HTML email report for a multi-hive apiary. Reads inspection, mite,
queen rearing, and harvest data from a Google Sheet, scores each hive by risk, and
emails a formatted report every Sunday morning.

#### How it works

```
Google Sheet (live data)
        ↓
  src/ingest.py       — reads 9 sheets via Google Sheets API
  src/analysis.py     — scores each hive: strength, queen status, mite pressure, risk
  src/seasonal.py     — month-aware advice + triggered rules
  src/report_builder.py — Jinja2 HTML render
  src/email_sender.py — Gmail SMTP send
        ↓
Weekly HTML email + reports/YYYY-MM-DD.html archive
```

#### Setup

**Prerequisites**
- Python 3.11+
- A Google Cloud service account with the Sheets API enabled and Viewer access to the spreadsheet
- A Gmail account with an App Password

**1. Clone and install**
```bash
git clone https://github.com/johnpiazza1/Turin-Family-Farm.git
cd Turin-Family-Farm/beehive-command
pip install -r requirements.txt
```

**2. Create `.env`** (copy from `.env.example` and fill in values)
```
SPREADSHEET_ID=<from the Google Sheet URL>
SERVICE_ACCOUNT_JSON=/path/to/service-account-key.json
APIARY_NAME=Turin Family Farm Apiary
EMAIL_FROM=you@gmail.com
EMAIL_TO=you@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

**3. Test**
```bash
python main.py --dry-run      # generates HTML, opens in browser
python main.py --test-email   # sends report to EMAIL_FROM
python main.py                # sends report to EMAIL_TO
```

#### Scheduling

**GitHub Actions (recommended)** — runs in the cloud, no local machine needed.
Set these repository secrets in GitHub → Settings → Secrets:

| Secret | Value |
|--------|-------|
| `SPREADSHEET_ID` | Google Sheet ID from the URL |
| `SERVICE_ACCOUNT_JSON_B64` | `base64 -w0 service-account.json` output |
| `EMAIL_FROM` | Gmail address |
| `EMAIL_TO` | Recipient address |
| `GMAIL_APP_PASSWORD` | 16-character Gmail App Password |

The workflow runs every Sunday at 8 AM EDT. You can also trigger it manually from
the GitHub Actions tab.

**Windows Task Scheduler** — alternative if you prefer local execution.
Run `schedule_windows.ps1` as Administrator to register a Sunday 8 AM job.

#### Report sections

1. Header — apiary name, date, active hive count, total bee frames, alert count
2. Alerts panel — hives needing immediate attention (OVERDUE, QUEENLESS, etc.)
3. Hive cards — one per hive: strength, queen status, days since inspection, mite pressure, risk score
4. Queen rearing timeline — active Nicot batches and larvae transfers
5. Mite pressure summary — all hives with rates, trend (↑/↓/→), and treatment status
6. Seasonal recommendations — month-aware advice plus triggered rules
7. Honey harvest YTD — total weight by hive
8. Footer — timestamp + link to Google Sheet
