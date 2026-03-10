import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


SMTP_HOST = "smtp.ethereal.email"
SMTP_PORT = 587
SMTP_USER = "americo28@ethereal.email"  
SMTP_PASS = "8jSS8STyM6MMkJYT4A"  

def send_email(to,subject,body):
    if not SMTP_USER or not SMTP_PASS:
        # Mock: just print
        print(f"[EMAIL MOCK] To: {to} | Subject: {subject}")
        return True

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to, msg.as_string())

        print(f"[EMAIL SENT] To: {to}")
        return True
    except Exception as e:
        print(f"[EMAIL FAILED] {e}")
        return False

if __name__=="__main__":
    send_email("hi@example.com", "Test", "Hello from Price Tool. How are you Doing!")