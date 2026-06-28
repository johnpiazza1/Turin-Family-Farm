from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def _plain_fallback(html: str) -> str:
    import re
    text = re.sub(r"<[^>]+>", "", html)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def send_report(html: str, config, subject: str | None = None) -> None:
    if subject is None:
        from datetime import date
        subject = f"{config.apiary_name} — Weekly Report {date.today().strftime('%b %d, %Y')}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.email_from
    msg["To"] = config.email_to

    msg.attach(MIMEText(_plain_fallback(html), "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(config.email_from, config.gmail_app_password)
        smtp.sendmail(config.email_from, config.email_to, msg.as_string())

    print(f"Report sent to {config.email_to}")
