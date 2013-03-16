from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email_creds import EMAIL_CREDENTIALS, TO_ADDRS
import smtplib
import sys
from traceback import print_tb

SENDER = 'El Kayak Monitore'

session = None

def setup_session():
    global session
    if session:
        try:
            session.quit()
        except Exception, e:
            print 'Error quitting session (continuing anyway):', e
            _, _, tb = sys.exc_info()
            print_tb(tb)
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

    for _ in xrange(5):
        try:
            session.sendmail(msg['From'], msg['To'].split(', '), msg.as_string())
        except smtplib.SMTPServerDisconnected:
            setup_session()
        else:
            break
