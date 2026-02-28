import smtplib
from email.message import EmailMessage
import os

def send_email(subject, body):
    sender = os.environ.get("ALERT_EMAIL")
    password = os.environ.get("ALERT_PASSWORD")
    receiver = os.environ.get("RECEIVER_EMAIL")

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.send_message(msg)