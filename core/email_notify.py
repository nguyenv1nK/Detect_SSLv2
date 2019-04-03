import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from core.configuration import settings
from core.logger import logger


def sent_email(message, sender=settings.config["email_notify"]["sender"],
               receivers=settings.config["email_notify"]["receivers"]):
    email = sender["email"]
    password = sender["password"]
    server = sender["server"]
    port = sender["port"]
    subject = sender["subject"]
    try:
        smtpObj = smtplib.SMTP(server, port)
        smtpObj.ehlo()
        try:
            smtpObj.starttls()
        except Exception as ex:
            pass
        smtpObj.login(email, password)#.decode("rot13"))
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = email
        for _email in receivers:
            msg['To'] = _email
            msg.attach(MIMEText(message, 'html', "utf-8"))
            smtpObj.sendmail(email, _email, msg.as_string())
            logger.log("Successfully sent email: " + str(_email), plugin="email notify")
    except smtplib.SMTPException:
        logger.error("Error: unable to send email", plugin="email notify")


if __name__ == '__main__':
    sent_email(message="<br/>Test email")
