"""
    Little module to speed up the testing
"""
import os, sys, time, string, smtplib, requests, json, itertools
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

URL = 'http://64675ace.ngrok.io'

lstPlayers = ["brad.hontz@pinpointview.com","gthontz@gmail.com","danielle.hontz@gmail.com","athontz@gmail.com"]
lstPlayerIDs = [1157, 6983, 6042, 4993]

"""
    taken from: https://makina-corpus.com/blog/metier/2016/the-worlds-simplest-python-template-engine
    Using this to add conditional capability to templating
"""
class SuperFormatter(string.Formatter):

    def format_field(self, value, spec):
        if spec.startswith('if'):
            return (value and spec.partition(':')[-1]) or ''
        else:
            return super(SuperFormatter, self).format_field(value, spec)

def SimpleEmailMessage(strToPerson, subject, html, text, lstAttachments):
    """
        Here we're using some of python's standard methods to send a simple email.
        I didn't finish this as you need to add your gmail account pw to make this work.
        Left it in here for you to discover and fix up.
    """
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = 'bhontz@gmail.com'
    msg['To'] = strToPerson

    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html, 'html'))

    # provides a mean for attachment of files
    if lstAttachments != []:
        for f in lstAttachments:
            with open(f, "rb") as fil:
                part = MIMEApplication(fil.read(), Name=os.path.basename(f))
                # After the file is closed  NOT SURE IF I NEED TO EXPLICITY CLOSE THE FP IF THERE ARE MULTIPLE FILES (need to test) ...
                part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(f)
                msg.attach(part)
                fil.close()

    try:
        smtpObj = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        smtpObj.ehlo()
        smtpObj.login('bhontz@gmail.com', 'Sc00byD00')
        smtpObj.sendmail('bhontz@gmail.com', strToPerson,
                         msg.as_string())  # this could be a list of addresses to loop over with a pause in between
        smtpObj.close()
        del smtpObj
        print('Email Sent to: %s' % strToPerson)
        time.sleep(5)  # let the server rest
    except smtplib.SMTPAuthenticationError as ex:
        print("SMTP Authentication Error: ", ex)

    return

if __name__ == '__main__':
    print("hello from module %s. Python version: %s" % (sys.argv[0], sys.version))
    sys.stdout.write("--------------------------------------------------------------\n")
    sys.stdout.write("Start of %s Process: %s\n\n" % (sys.argv[0], time.strftime("%H:%M:%S", time.localtime())))

    sf = SuperFormatter()
    r = dict()
    strSubject = "Five Crowns Game Invitation - GAME HAS STARTED!"

    for id, player in enumerate(lstPlayers):
        r["URL"] = URL
        r["ID"] = lstPlayerIDs[id]
        fp = open('GameInvitationEmail.html')
        html = fp.read()
        fp.close()
        html = sf.format(html, **r)
        SimpleEmailMessage(player, strSubject, html, html, [])

    sys.stdout.write("\n\nEnd of %s Process: %s.\n" % (
    sys.argv[0], time.strftime("%H:%M:%S", time.localtime())))
    sys.stdout.write("-------------------------------------------------------------\n")
