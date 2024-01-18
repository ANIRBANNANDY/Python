import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send_email(email_config):
    smtp_server = email_config.get("smtp_server")
    smtp_port = email_config.get("smtp_port")
    sender_email = email_config.get("sender_email")
    sender_password = email_config.get("sender_password")

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(sender_email, sender_password)

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email_config["recipient_email"]
    msg['Subject'] = 'Multiple Attachments'

    for attachment in email_config["attachments"]:
        attach_file = open(attachment, 'rb')
        payload = MIMEBase('application', 'octate-stream')
        payload.set_payload((attach_file).read())
        encoders.encode_base64(payload)
        payload.add_header('Content-Disposition', f'attachment; filename={attachment}')
        msg.attach(payload)

    text = "Please find the attached files."
    msg.attach(MIMEText(text, 'plain'))

    server.send_message(msg)
    del msg

    server.quit()

if __name__ == "__main__":
    with open('email_config.json') as f:
        email_configs = json.load(f)

    for email_config in email_configs["email_configurations"]:
        send_email(email_config)
