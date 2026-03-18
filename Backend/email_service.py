# Backend/email_service.py
from typing import Optional
from tasks import send_email_task


def queue_email(to_email: Optional[str], subject: str, body: str) -> Optional[str]:
    """
    Returns Celery task_id if queued, else None.
    IMPORTANT: This means "queued", not "sent".
    """
    if not to_email:
        return None
    try:
        result = send_email_task.delay(to_email, subject, body)
        return result.id
    except Exception as e:
        print(f"[WARN] Failed to queue email to {to_email}: {e}")
        return None