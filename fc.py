from PyQt5.QtWidgets import (QLabel, QScrollArea, QDesktopWidget, QPushButton, QDialog, QVBoxLayout, QGridLayout, QGroupBox, QApplication, QLineEdit, QHBoxLayout)
from PyQt5.QtGui import QPixmap, QDrag, QPainter
from PyQt5.QtCore import QMimeData, Qt, QSize
from PyQt5 import QtCore
import os, sys, time, itertools, functools, json, requests
from urllib.parse import quote
from flask import Flask, render_template_string
from FiveCrownsPlayer import Player

# used during development, obsolete
# theURL = "http://localhost:5000/" "http://e90fecd0.ngrok.io/"  #"http://192.168.100.35:5000/" # "http://localhost:5000/"

@functools.lru_cache()
class GlobalObject(QtCore.QObject):
    """
        using this so my parent window knows a drop happening in the child
    """
    def __init__(self):
        super().__init__()
        self._events = {}
        self.gameURL = None
        self.thisPlayer = None
        self.dictResponse = None

    def addEventListener(self, name, func):
        if name not in self._events:
            self._events[name] = [func]
        else:
            self._events[name].append(func)

    def dispatchEvent(self, name):
        functions = self._events.get(name, [])
        for func in functions:
            QtCore.QTimer.singleShot(0, func)

    def receiveResponse(self, jsonResponse):
        if jsonResponse:
            self.dictResponse = eval(jsonResponse.content)
            print("FROM SERVER:\n{}".format(self.dictResponse))
            self.__updateThisPlayer()

            self.playerMessage()
            self.showDiscard()
            self.updateHand()

            if "activePlayer" in self.dictResponse.keys():
                if self.thisPlayer.name == self.dictResponse["activePlayer"]:
                    if not self.thisPlayer.hasExtraCard and not self.thisPlayer.hasDiscarded:
                        # print("calling PlayerDraw Dialog with extraCard:{} and hasDiscarded:{}".format(self.thisPlayer.hasExtraCard, self.thisPlayer.hasDiscarded))
                        dlg = PlayerDraw()
                        if not dlg.exec_():
                            pass
                            # print("DIALOG: canceled PlayerDraw")
                    elif self.thisPlayer.hasDiscarded:
                        # print("calling PlayerPass Dialog with extraCard:{} and hasDiscarded:{}".format(self.thisPlayer.hasExtraCard, self.thisPlayer.hasDiscarded))
                        dlg = PlayerPass()
                        if not dlg.exec_():
                            pass
                            # print("DIALOG: canceled PlayerPass")

        return

    def playerMessage(self):
        self.dispatchEvent("playerMessage")
        return

    def showDiscard(self):
        if self.dictResponse["round"]:
            self.dispatchEvent("showDiscard")
        return

    def updateHand(self):
        if "activePlayer" in self.dictResponse.keys() and self.thisPlayer.name == self.dictResponse["activePlayer"]:
            self.dispatchEvent("updateHand")
        elif "roundOver" in self.dictResponse.keys():
            self.dispatchEvent("outHand")
        return

    def getPlayerId(self):
        return self.thisPlayer.id

    def getServerURL(self):
        """
            TODO: need to get this from somewhere
        """
        return self.gameURL

    def __updateThisPlayer(self):
        """
            The player in the global object has fields that need to be updated from server responses
        """
        if "activePlayer" in self.dictResponse.keys() and self.thisPlayer.name == self.dictResponse["activePlayer"]:
            self.thisPlayer.hasExtraCard = self.dictResponse["hasExtraCard"]
            self.thisPlayer.hasDiscarded = self.dictResponse["hasDiscarded"]

class EndGame(QDialog):
    """
        quit
    """
    def __init__(self, parent=None, flags=Qt.WindowFlags()):
        super().__init__(parent=parent, flags=flags)
        self.gObj = GlobalObject()
        flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.initUI()

    def initUI(self):
        dlgMsg = QLabel(self)
        dlgMsg.setText("Thanks for playing {}!".format(self.gObj.thisPlayer.name))

        btnNextRound = QPushButton("Close")
        btnNextRound.clicked.connect(self.endItAll)
        vBox = QVBoxLayout()
        vBox.addStretch(1)
        vBox.addWidget(dlgMsg, 10)
        vBox.addWidget(btnNextRound, 90)
        self.setLayout(vBox)

        self.resize(225, 155)
        self.__centerOnScreen()
        self.setWindowTitle("GAME OVER")
        self.show()

    def __centerOnScreen(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def endItAll(self, event):
        self.gObj.dispatchEvent("kamikazi")
        self.close()

class Dealer(QDialog):
    """
        exposed ONLY TO THE DEALER at the start the next round
    """
    def __init__(self, parent=None, flags=Qt.WindowFlags()):
        super().__init__(parent=parent, flags=flags)
        self.gObj = GlobalObject()
        flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.initUI()

    def initUI(self):
        dlgMsg = QLabel(self)
        dlgMsg.setText("Review hands, then click to start the next round".format(self.gObj.thisPlayer.name))

        btnNextRound = QPushButton("Start Round {}".format(self.gObj.dictResponse["round"] + 1))
        btnNextRound.clicked.connect(self.startNextRound)
        vBox = QVBoxLayout()
        vBox.addStretch(1)
        vBox.addWidget(dlgMsg, 10)
        vBox.addWidget(btnNextRound, 90)
        self.setLayout(vBox)

        # self.setGeometry(0, 0, 200, 150)  # put this in the corner so you can scroll main window
        self.resize(200, 150)
        self.__centerOnScreen()
        self.setWindowTitle("You\'re the Dealer")
        self.show()

    def __centerOnScreen(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def startNextRound(self, event):
        self.close()
        self.update()
        strMsg = "{}nextround?id={}".format(self.gObj.getServerURL(), self.gObj.getPlayerId())
        self.gObj.receiveResponse(requests.get(strMsg))
        # self.close()   # close was down here ...

class PlayerPass(QDialog):
    def __init__(self, parent=None, flags=Qt.WindowFlags()):
        super().__init__(parent=parent, flags=flags)
        self.gObj = GlobalObject()
        flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.initUI()

    def initUI(self):
        dlgMsg = QLabel(self)
        dlgMsg.setText("{}, Pass or Out?".format(self.gObj.thisPlayer.name))

        btnPass = QPushButton("I pass")
        if "outPlayer" in self.gObj.dictResponse.keys():
            btnPass.setEnabled(False)
        btnPass.clicked.connect(self.clickedPass)
        orMsg = QLabel(self)
        orMsg.setText("  OR  ")
        btnOut = QPushButton("I\'m out!")
        btnOut.clicked.connect(self.clickedOut)
        hBox = QHBoxLayout()
        hBox.addStretch(1)
        hBox.addWidget(btnPass)
        hBox.addWidget(orMsg)
        hBox.addWidget(btnOut)

        vBox = QVBoxLayout()
        vBox.addWidget(dlgMsg, 10)
        vBox.addLayout(hBox, 90)
        self.setLayout(vBox)

        self.resize(200, 150)
        self.__centerOnScreen()
        self.setWindowTitle("Player Action Required")
        self.show()

    def __centerOnScreen(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def clickedPass(self, event):
        self.close()
        self.update()
        strMsg = "{}pass?id={}".format(self.gObj.getServerURL(), self.gObj.getPlayerId())
        self.gObj.receiveResponse(requests.get(strMsg))

    def clickedOut(self, event):
        """
            when a player goes out, we send his local hand back to the server via player.outhand
        """
        self.close()
        self.update()
        strMsg = "{}out?id={}&outhand={}".format(self.gObj.getServerURL(), self.gObj.getPlayerId(), json.dumps(self.gObj.thisPlayer.outhand))
        # print("UI-clickedOut\n{}".format(strMsg))
        self.gObj.receiveResponse(requests.get(strMsg))
        self.gObj.dispatchEvent("outHand")   # try moving this to start of new round

class PlayerDraw(QDialog):
    def __init__(self, parent=None, flags=Qt.WindowFlags()):
        super().__init__(parent=parent, flags=flags)
        self.gObj = GlobalObject()
        flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.initUI()

    def initUI(self):
        msg = QLabel(self)
        msg.setText("Click to Draw from Deck or Discard Pile")
        deck = QLabel(self)
        deck.setPixmap(QPixmap("cardimages/0_0.svg"))
        deck.mouseReleaseEvent = self.clickedDeck
        orMsg = QLabel(self)
        orMsg.setText("  OR  ")
        discard = QLabel(self)
        d = eval(self.gObj.dictResponse["discard"])
        imageName = "cardimages/{}_{}.svg".format(d["suit"], d["value"])
        discard.setPixmap(QPixmap(imageName))
        discard.mouseReleaseEvent = self.clickedDiscard
        hBox = QHBoxLayout()
        hBox.addStretch(1)
        hBox.addWidget(deck)
        hBox.addWidget(orMsg)
        hBox.addWidget(discard)
        vBox = QVBoxLayout()
        vBox.addWidget(msg, 10)
        vBox.addLayout(hBox, 90)
        self.setLayout(vBox)

        self.resize(200, 150)
        self.__centerOnScreen()
        self.setWindowTitle("IT\'s YOUR TURN!")
        self.show()

    def __centerOnScreen(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def clickedDeck(self, event):
        self.close()
        self.update()
        strMsg = "{}pickDeck?id={}".format(self.gObj.getServerURL(), self.gObj.getPlayerId())
        # print("draw from deck".format(strMsg))
        self.gObj.receiveResponse(requests.get(strMsg))
        # self.close()

    def clickedDiscard(self, event):
        self.close()
        self.update()
        strMsg = "{}pickDiscard?id={}".format(self.gObj.getServerURL(), self.gObj.getPlayerId())
        # print("draw from discard".format(strMsg))
        self.gObj.receiveResponse(requests.get(strMsg))
        # self.close()

class PlayerCheckIn(QDialog):

    def __init__(self):
        super().__init__()
        self.playerURL = QLineEdit(self)
        self.playerName = QLineEdit(self)
        self.gObj = GlobalObject()
        self.initUI()

    def initUI(self):
        promptLabel = QLabel(self)
        promptLabel.setText("Paste the URL from the EMAIL INVITATION:")
        nameLabel = QLabel(self)
        nameLabel.setText("Enter your name:")
        self.btnSubmit = QPushButton("Submit")
        self.btnSubmit.clicked.connect(self.__playerCheckIn)

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.btnSubmit)

        vbox = QVBoxLayout()
        vbox.addWidget(promptLabel,1)
        vbox.addWidget(self.playerURL)
        vbox.addWidget(nameLabel, 1)
        vbox.addWidget(self.playerName)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

        self.resize(500, 150)
        self.__centerOnScreen()
        self.setWindowTitle('Player Check In')

        self.show()

    def __centerOnScreen(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def __playerCheckIn(self):
        # load up the URL we came from
        s = self.playerURL.text().strip()
        n = s.find("playerReady")
        self.gObj.gameURL = s[:n]
        print("s:{} n:{} gameURL:{}".format(s, n, self.gObj.gameURL))

        strCheckIn = "{}&name={}".format(s, quote(self.playerName.text()))
        print("DIALOG PlayerCheckIn:\n{} just checked In".format(strCheckIn))
        response = requests.get(strCheckIn)
        # in this case, we're going to pull the id right away so we can create the GlobalObject thisPlayer
        if response:
            d = eval(response.content)
            if "id" in d.keys():
                self.gObj.thisPlayer = Player(self.playerName.text(), d["id"])
                self.gObj.receiveResponse(response)

        self.close()

class CardIcon(QLabel):

    def __init__(self, item, parent):
        super().__init__(item, parent)

        self.setAcceptDrops(True)
        self.d = eval(item)
        imageName = "cardimages/{}_{}.svg".format(self.d["suit"], self.d["value"])
        self.setPixmap(QPixmap(imageName))
        self.show()

    def exposeCard(self):
        return self.d

    def updateImage(self, item):
        """
            item is json representation of Card()
        """
        self.d = eval(item)
        imageName = "cardimages/{}_{}.svg".format(self.d["suit"],self.d["value"])
        self.setPixmap(QPixmap(imageName))
        self.show()
        return

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
        drag = QDrag(self)
        mimedata = QMimeData()
        mimedata.setText(json.dumps(self.d))
        mimedata.setImageData(self.pixmap().toImage())

        drag.setMimeData(mimedata)
        pixmap = QPixmap(self.size())
        painter = QPainter(pixmap)
        painter.drawPixmap(self.rect(), self.grab())
        painter.end()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())
        drag.exec_(Qt.CopyAction | Qt.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    @QtCore.pyqtSlot()
    def dropEvent(self, event):
        pos = event.pos()
        if event.mimeData().hasText():
            text = event.mimeData().text()
            self.d = eval(text)
            imageName = "cardimages/{}_{}.svg".format(self.d["suit"], self.d["value"])
            self.setPixmap(QPixmap(imageName))
            self.show()
            event.acceptProposedAction()
            GlobalObject().dispatchEvent("dropCard")

class CardDiscardIcon(CardIcon):
    def __init__(self, item, parent):
        super().__init__(item, parent)

    def mousePressEvent(self, event):
        return

    def mouseMoveEvent(self, event):
        return

    def dropEvent(self, event):
        qObj = GlobalObject()
        if qObj.thisPlayer.hasExtraCard and not qObj.thisPlayer.hasDiscarded:
            pos = event.pos()
            if event.mimeData().hasText():
                text = event.mimeData().text()
                self.d = eval(text)
                imageName = "cardimages/{}_{}.svg".format(self.d["suit"], self.d["value"])
                self.setPixmap(QPixmap(imageName))
                self.show()
                event.acceptProposedAction()
                strDiscard = "{}discard?id={}&card={}".format(qObj.getServerURL().strip(), qObj.getPlayerId(), json.dumps(text))
                # print("Player is discarding:{}".format(strDiscard))
                response = requests.get(strDiscard)
                if response:
                    qObj.receiveResponse(response)

class App(QDialog):

    def __init__(self):
        super().__init__()
        self.title = 'Fivecrowns Player UI'
        self.width = 1200
        self.height = 800
        self.handGroupBox = QGroupBox("Player Hand:")
        self.gridHand = QGridLayout()
        self.msgText = QLabel()
        self.gObj = GlobalObject()
        self.cardArray = []
        self.cardIcons = []  # local hand, reordered from server's copy
        self.discardCardIcon = CardDiscardIcon(json.dumps({"suit":0, "value":0}), self)
        self.gObj.addEventListener("dropCard", self.cardMoved)
        self.gObj.addEventListener("playerMessage", self.__playerMessage)
        self.gObj.addEventListener("showDiscard", self.__showDiscard)
        self.gObj.addEventListener("updateHand", self.__playerHand)
        self.gObj.addEventListener("outHand", self.__outHand)
        self.gObj.addEventListener("kamikazi", self.__endGame)
        self.flaskApp = Flask(self.title)

        dlg = PlayerCheckIn()  # present at app launch
        if not dlg.exec_():
            pass
            # print("DIALOG: canceled PlayerCheckIn")

        self.initUI()

    def __del__(self):
        del self.flaskApp
        self.flaskApp = None
        del self.cardArray
        del self.cardIcons

    def initUI(self):
        self.setWindowTitle(self.title)
        # self.setGeometry(self.left, self.top, self.width, self.height)
        self.resize(self.width, self.height)
        self.__centerOnScreen()

        self.vrtMain = QVBoxLayout() # self.verticalLayoutWidget
        self.vrtMain.setContentsMargins(0, 0, 0, 0)
        self.vrtMain.setObjectName("vrtMain")

        self.hzMsgDiscard = QHBoxLayout()
        self.hzMsgDiscard.setObjectName("hzMsgDiscard")

        self.grpMessage = QGroupBox()
        self.grpMessage.setObjectName("grpMessage")
        self.grpMessage.setTitle("Message:")
        # self.msgText = QLabel()
        self.msgText.setTextFormat(Qt.RichText)
        self.msgText.setMinimumSize(800,1200) # was 800, 800
        self.__playerMessage()
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(self.msgText)
        scrollArea.ensureWidgetVisible(self.msgText)
        scrollArea.setAlignment(Qt.AlignTop)

        msgGrid = QGridLayout()
        msgGrid.addWidget(scrollArea)
        self.grpMessage.setLayout(msgGrid)

        self.hzMsgDiscard.addWidget(self.grpMessage, 90)

        self.vrtSubmitDiscard = QVBoxLayout()
        self.vrtSubmitDiscard.setObjectName("vrtSubmitDiscard")

        self.btnRefresh = QPushButton()
        self.btnRefresh.setObjectName("btnRefresh")
        self.btnRefresh.setText("Refresh")
        self.btnRefresh.clicked.connect(lambda: self.__playerStatus(self.gObj.getPlayerId()))
        self.vrtSubmitDiscard.addWidget(self.btnRefresh)

        self.grpDiscard = QGroupBox()
        self.grpDiscard.setObjectName("grpDiscard")
        self.grpDiscard.setTitle("Discard:")
        discardGrid = QGridLayout()
        discardGrid.addWidget(self.discardCardIcon)
        self.grpDiscard.setLayout(discardGrid)
        self.vrtSubmitDiscard.addWidget(self.grpDiscard)
        self.hzMsgDiscard.addLayout(self.vrtSubmitDiscard, 10)
        self.vrtMain.addLayout(self.hzMsgDiscard, 40)

        grpHand = QGroupBox("Player Hand:")
        self.__playerHand()
        grpHand.setLayout(self.gridHand)
        self.vrtMain.addWidget(grpHand)

        self.setLayout(self.vrtMain)
        self.show()

    def __centerOnScreen(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def __playerStatus(self, playerId):
        strStatus = "{}playerStatus?id={}".format(self.gObj.getServerURL(), self.gObj.getPlayerId())
        self.gObj.receiveResponse(requests.get(strStatus))
        return

    @QtCore.pyqtSlot()
    def __playerMessage(self):
        """
            Updates the message box
        """
        if self.gObj.dictResponse:
            dMsg = {}
            d = self.gObj.dictResponse
            if "roundOver" in d.keys():
                for k, v in d.items():
                    if k == "playerHands":
                        lstPlayers = json.loads(v)
                        lstInner = []
                        for p in lstPlayers:
                            dInner = {}
                            dInner["name"] = p["name"]
                            dInner["outHand"] = eval(p["outHand"])
                            lstInner.append(dInner)
                        dMsg["playerHands"] = lstInner
                    else:
                        dMsg[k] = v
                msg = self.__htmlMessage("roundOver.html", dMsg)
                self.msgText.setText(msg)  # don't move this below the if/then/else tree

                if "gameOver" in d.keys():
                    dlg = EndGame()  # kill it off
                    if not dlg.exec_():
                        pass

                elif "name" in d.keys() and "dealer" in d.keys():
                    if d["name"] == d["dealer"]:
                        dlg = Dealer()  # present the ability to advance round to the dealer
                        if not dlg.exec_():
                            pass

            elif not d["round"]:
                left = d["startGameAfterCheckIns"] - d["checkIns"]
                dMsg = dict(name=d["name"], left=left)
                msg = self.__htmlMessage("checkedIn.html", dMsg)
                self.msgText.setText(msg)  # don't move this below the if/then/else tree

            else:
                msg = self.__htmlMessage("playerStatus.html", d)
                self.msgText.setText(msg)  # don't move this below the if/then/else tree

        else:  # checked in player waiting on start of game
            msg = "<html><body><h1>Welcome to Five Crowns!</h1></body></html>"
            self.msgText.setText(msg)

        return

    @QtCore.pyqtSlot()
    def __showDiscard(self):
        if self.gObj.dictResponse:
            d = self.gObj.dictResponse
            if d["round"]:
                self.discardCardIcon.updateImage(d["discard"])

        return

    @QtCore.pyqtSlot()
    def __playerHand(self):
        """
            syncs player's local hand with server, accounting for changes and retaining local hand order
            TODO: local hand needs to wipe when the round changes
        """

        if self.gObj.dictResponse:
            serverHand = eval(self.gObj.dictResponse["hand"])
            # print("HAND:\nserver:{} local:{}".format(serverHand, self.cardArray))
            if len(serverHand) > len(self.cardArray):
                inServerNotLocal = list(itertools.filterfalse(lambda i: i in self.cardArray, serverHand))
                self.cardArray.extend(inServerNotLocal)
                print("inServerNotLocal:{}".format(inServerNotLocal))
            else:
                inLocalNotServer = list(itertools.filterfalse(lambda i: i in serverHand, self.cardArray))
                for card in inLocalNotServer:
                    self.cardArray.remove(card)
                # print("inLocalNotServer:{}".format(inLocalNotServer))

            self.cardIcons = []

            # you have to kill off the grid widgets and add them back in using this technique
            for i in reversed(range(self.gridHand.count())):
                widgetToRemove = self.gridHand.itemAt(i).widget()
                widgetToRemove.setParent(None)
                widgetToRemove.deleteLater()

            row = 0
            col = 0
            for i, card in enumerate(self.cardArray):
                s = json.dumps(card)
                self.cardIcons.append(CardIcon(s, self))
                if i and not (i % 4):   # 4 cards per row max,
                    row += 1
                    col = 0
                self.gridHand.addWidget(self.cardIcons[i], row, col)  # gotta do something here when i > 7
                col += 1

            self.gObj.thisPlayer.outhand = list(self.cardArray)

        return

    def __reorderHand(self):
        """
            entire local hand is reordered when user drops a card in a new location
        """
        if self.cardIcons:
            for destIdx, card in enumerate(self.cardIcons):
                card = card.exposeCard()
                if card != self.cardArray[destIdx]:
                    break

            sourceIdx = self.cardArray.index(card)
            # print("destIdx:{} sourceIdx:{} sourceCard:{}".format(destIdx, sourceIdx, card))
            card = self.cardArray.pop(sourceIdx)
            self.cardArray.insert(destIdx, card)

            for i, card in enumerate(self.cardIcons):   # update all cards and local deck
                card.updateImage(json.dumps(self.cardArray[i]))
            # print("after: {}".format(self.cardArray))

            self.gObj.thisPlayer.outhand = list(self.cardArray) # keep the local hand ordering here for when the player goes out

        return

    @QtCore.pyqtSlot()
    def __outHand(self):
        """
           clear the local hand after going out (server already received the "outhand")
        """
        self.cardArray = []
        self.cardIcons = []

        for i in reversed(range(self.gridHand.count())):
            widgetToRemove = self.gridHand.itemAt(i).widget()
            widgetToRemove.setParent(None)
            widgetToRemove.deleteLater()

        return

    def __htmlMessage(self, fileName, dMsg):
        """
            reads an HTML template file as a string, populates it with dMsg, and returns the string
        """
        s = "<html><body>Error reading file template</body></html>"
        try:
            fp = open("html/{}".format(fileName), "rt")
        except IOError as detail:
            s = "<html><body>Error {} reading file template {}</body></html>".format(detail, fileName)
        else:
            s = fp.read()
            fp.close()
            with self.flaskApp.app_context():
                s = render_template_string(s, template=dMsg)

        return s

    @QtCore.pyqtSlot()
    def cardMoved(self):
        self.__reorderHand()

        return

    @QtCore.pyqtSlot()
    def __endGame(self):
        self.close()
        sys.exit(0)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())