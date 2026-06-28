import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    excel_path: str
    apiary_name: str
    email_from: str
    email_to: str
    gmail_app_password: str


def load_config() -> Config:
    missing = []
    required = ["EXCEL_PATH", "EMAIL_FROM", "EMAIL_TO", "GMAIL_APP_PASSWORD"]
    for key in required:
        if not os.getenv(key):
            missing.append(key)
    if missing:
        raise EnvironmentError(
            f"Missing required .env variables: {', '.join(missing)}\n"
            "Copy .env.example to .env and fill in the values."
        )

    path = os.environ["EXCEL_PATH"]
    if not Path(path).exists():
        raise FileNotFoundError(f"Excel file not found: {path}")

    return Config(
        excel_path=path,
        apiary_name=os.getenv("APIARY_NAME", "Apiary"),
        email_from=os.environ["EMAIL_FROM"],
        email_to=os.environ["EMAIL_TO"],
        gmail_app_password=os.environ["GMAIL_APP_PASSWORD"],
    )
