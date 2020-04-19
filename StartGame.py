"""
    Use this module to create a new game.  This process entails knowing where the game engine
    is hosted (it's URL) and knowing the emails of the players you wish to invite.  You can
    also decide to start the game with fewer than the number of players you've invited, in
    the event you feel you'll have some "no shows"
"""
import os, sys, time, string, smtplib, pycurl, json
from io import BytesIO
from configparser import ConfigParser
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

"""
    *** NOTE *** 
    You need to modify the two variables below before running this process!
    Be sure your URL string ends with the '/' character.
"""

URL = 'http://localhost:8080/'
# lstPlayers = ["brad.hontz@pinpointview.com","bhontz@gmail.com"]
lstPlayers = ["brad.hontz@pinpointview.com", "gthontz@gmail.com", "danielle.hontz@gmail.com", "josephlyon87@gmail.com", "athontz@gmail.com"]

class SuperFormatter(string.Formatter):
    """
        taken from: https://makina-corpus.com/blog/metier/2016/the-worlds-simplest-python-template-engine
        Using this to add (very simplistic) condidtional capability to templating.
        The FLASK template engine is a good one to use if you need something more complex.
    """
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
        NOTE: using ConfigParser to load emailcredentials.ini, which IS EXCLUDED
        from the GitHub repository
    """

    cfg = ConfigParser()
    cfg.read('emailcredentials.ini')  # NEEDS TO BE IN THIS FOLDER!!!

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
        smtpObj.login(cfg.get('email','user'), cfg.get('email','pwd'))   # Credentials found in local file emailcredentials.ini
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

    """
        first start the game
    """
    payload = dict(invite=lstPlayers, startGameAfter=len(lstPlayers))
    strJSON = "data={}".format(json.dumps(payload))
    buffer = BytesIO()
    curl = pycurl.Curl()
    curl.setopt(pycurl.URL, URL + "createGame")
    print("strJSON: {}".format(strJSON))
    curl.setopt(pycurl.POSTFIELDS, strJSON)
    curl.setopt(pycurl.WRITEDATA, buffer)
    curl.perform()
    status_code = curl.getinfo(pycurl.RESPONSE_CODE)
    if status_code != 200:
        print("Aww Snap :( Server returned HTTP status code {}".format(status_code))
    else:
        response = buffer.getvalue()
        print("Server Response: {}".format(response.decode('iso-8859-1')))

    curl.close()
    time.sleep(5)  # wait abit for the server to get settled
    """
        now return the ids
    """
    curl = pycurl.Curl()
    buffer = BytesIO()
    curl.setopt(pycurl.URL, URL + "peakIds")
    curl.setopt(pycurl.WRITEDATA, buffer)
    curl.perform()
    status_code = curl.getinfo(pycurl.RESPONSE_CODE)
    if status_code != 200:
        print("Aww Snap :( Server returned HTTP status code {}".format(status_code))
    else:
        response = buffer.getvalue()
        print("Server Response: {}".format(response.decode('iso-8859-1')))
        lstPlayerIDs = eval(response.decode('iso-8859-1'))

    curl.close()

    time.sleep(5)  # wait abit for the server to get settled

    """
        now send the email invitations
    """
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