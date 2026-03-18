from celery_app import celery_app
import os
import smtplib
from email.mime.text import MIMEText


SMTP_HOST = os.getenv("SMTP_HOST", "smtp.ethereal.email")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "no-reply@example.com")


def _smtp_send(to_email: str, subject: str, body: str) -> None:
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        if SMTP_USER and SMTP_PASSWORD:
            server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, [to_email], msg.as_string())


@celery_app.task(name="email.send", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def send_email_task(to_email: str, subject: str, body: str) -> str:
    _smtp_send(to_email, subject, body)
    return f"queued->sent: {to_email}"