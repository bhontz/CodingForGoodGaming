"""
    Little module to speed up the testing
"""
import os, sys, time, requests, json

url = "http://localhost:5000/"
payload = {'data': {'invite': ['bhontz@gmail.com', 'brad.hontz@pinpointview.com'], 'startGameAfter': 2}}
headers = {"content-type": "text/html; charset=utf-8"}

if __name__ == '__main__':
    print("hello from module %s. Python version: %s" % (sys.argv[0], sys.version))
    sys.stdout.write("--------------------------------------------------------------\n")
    sys.stdout.write("Start of %s Process: %s\n\n" % (sys.argv[0], time.strftime("%H:%M:%S", time.localtime())))

    # peek at the ids of the 2 requested users
    response = requests.get(url+"peakIds")
    print(response.content)
    lstIds = eval(response.content)
    print(lstIds[0])

    # checkIn both requested users
    response = requests.get(url + "playerReady?id={}&name=Player1".format(lstIds[0]))
    print(response.content)
    response = requests.get(url + "playerReady?id={}&name=Player2".format(lstIds[1]))
    print(response.content)

    # player2 is active player, draw a card
    response = requests.get(url + "pickDeck?id={}&name=Player2".format(lstIds[1]))
    print(response.content)


    # j = json.loads(response.content)
    # print(j)
    # print(type(j))



    # response = requests.get(url+"playerStatus?id=317")
    # j = json.loads(response.content)
    # print(j)
    # print(type(j))

    sys.stdout.write("\n\nEnd of %s Process: %s.\n" % (
    sys.argv[0], time.strftime("%H:%M:%S", time.localtime())))
    sys.stdout.write("-------------------------------------------------------------\n")
