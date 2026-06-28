import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    spreadsheet_id: str
    service_account_json: str
    apiary_name: str
    email_from: str
    email_to: str
    gmail_app_password: str


def load_config() -> Config:
    missing = []
    required = ["SPREADSHEET_ID", "SERVICE_ACCOUNT_JSON", "EMAIL_FROM", "EMAIL_TO", "GMAIL_APP_PASSWORD"]
    for key in required:
        if not os.getenv(key):
            missing.append(key)
    if missing:
        raise EnvironmentError(
            f"Missing required .env variables: {', '.join(missing)}\n"
            "Copy .env.example to .env and fill in the values."
        )

    sa_path = os.environ["SERVICE_ACCOUNT_JSON"]
    if not Path(sa_path).exists():
        raise FileNotFoundError(
            f"Service account JSON not found: {sa_path}\n"
            "See README for how to create a GCP service account."
        )

    return Config(
        spreadsheet_id=os.environ["SPREADSHEET_ID"],
        service_account_json=sa_path,
        apiary_name=os.getenv("APIARY_NAME", "Apiary"),
        email_from=os.environ["EMAIL_FROM"],
        email_to=os.environ["EMAIL_TO"],
        gmail_app_password=os.environ["GMAIL_APP_PASSWORD"],
    )
