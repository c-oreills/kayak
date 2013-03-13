from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email_creds import EMAIL_CREDENTIALS, TO_ADDRS
SENDER = 'El Kayak Monitore'

session = None

def setup_session():
    global session
    import smtplib
    session = smtplib.SMTP('smtp.gmail.com', 587)
    session.ehlo()
    session.starttls()
    session.ehlo()
    session.login(*EMAIL_CREDENTIALS)

def sendmail(subject, body):
    if not session:
        setup_session()

    msg = MIMEMultipart()
    msg['From'] = SENDER
    msg['Subject'] = subject
    msg['To'] = ', '.join(TO_ADDRS)
    body = MIMEText(body)
    msg.attach(body)

    session.sendmail(msg['From'], msg['To'].split(', '), msg.as_string())
