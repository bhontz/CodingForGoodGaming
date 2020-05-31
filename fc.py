from PyQt5.QtWidgets import (QLabel, QScrollArea, QDesktopWidget, QPushButton, QDialog, QVBoxLayout, QGridLayout, QGroupBox, QApplication, QWidget, QLineEdit, QHBoxLayout)
from PyQt5.QtGui import QPixmap, QDrag, QPainter
from PyQt5.QtCore import QMimeData, Qt, QSize
from PyQt5 import QtCore
import os, sys, time, itertools, functools, json, requests, logging, jinja2
from urllib.parse import quote
from flask import Flask, render_template_string
from FiveCrownsPlayer import Player
from FiveCrownsGame import GroupType

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
        self.logger = logging.getLogger(__name__)
        fn = time.strftime("logs/%Y%m%d-%H%M%S.log", time.localtime())
        f_handler = logging.FileHandler(fn, mode="w")
        f_handler.setFormatter(logging.Formatter('%(asctime)s,%(levelname)s,%(message)s',datefmt="%Y%m%d-%H%M%S"))
        self.logger.addHandler(f_handler)
        self.logger.setLevel(logging.DEBUG)

    def __del__(self):
        handlers = self.logger.handlers[:]
        for handler in handlers:
            handler.close()
            self.logger.removeHandler(handler)

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
            self.logger.info(format(self.dictResponse))
            # print("FROM SERVER:\n{}".format(self.dictResponse))
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
                        del dlg
                    elif self.thisPlayer.hasDiscarded:
                        # print("calling PlayerPass Dialog with extraCard:{} and hasDiscarded:{}".format(self.thisPlayer.hasExtraCard, self.thisPlayer.hasDiscarded))
                        dlg = PlayerPass()
                        if not dlg.exec_():
                            pass
                            # print("DIALOG: canceled PlayerPass")
                        del dlg

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
        dialog to exit the game. leaving non-modal so you can scroll the final results
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.gObj = GlobalObject()
        self.initUI()

    def __del__(self):
        del self.gObj

    def initUI(self):
        dlgMsg = QLabel(self)
        dlgMsg.setText("Thanks for playing {}!".format(self.gObj.thisPlayer.name))

        btnNextRound = QPushButton("Exit Game")
        btnNextRound.clicked.connect(self.parent.closeEvent)
        vBox = QVBoxLayout()
        vBox.addStretch(1)
        vBox.addWidget(dlgMsg, 10)
        vBox.addWidget(btnNextRound, 90)
        self.setLayout(vBox)
        self.setGeometry(0, 0, 225, 155)  # put this in the corner so you can scroll main window
        self.setWindowTitle("GAME OVER")
        self.show()

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

    def __del__(self):
        del self.gObj

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
        self.setWindowModality(Qt.ApplicationModal)

    def __centerOnScreen(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def startNextRound(self, event):
        self.reject()
        strMsg = "{}nextround?id={}".format(self.gObj.getServerURL(), self.gObj.getPlayerId())
        self.gObj.receiveResponse(requests.get(strMsg))

class PlayerPass(QDialog):
    """
        Pass or I'm Out dialog
    """
    def __init__(self, parent=None, flags=Qt.WindowFlags()):
        super().__init__(parent=parent, flags=flags)
        self.parent = parent
        self.gObj = GlobalObject()
        flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.initUI()

    def __del__(self):
        del self.gObj

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
        self.setWindowModality(Qt.ApplicationModal)

    def __centerOnScreen(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def clickedPass(self, event):
        self.reject()
        strMsg = "{}pass?id={}".format(self.gObj.getServerURL(), self.gObj.getPlayerId())
        self.gObj.receiveResponse(requests.get(strMsg))

    def clickedOut(self, event):
        """
            when a player goes out, we send his local hand back to the server via player.outhand
        """
        self.reject()
        self.gObj.dispatchEvent("groupcards")

class PlayerDraw(QDialog):
    def __init__(self, parent=None, flags=Qt.WindowFlags()):
        super().__init__(parent=parent, flags=flags)
        self.gObj = GlobalObject()
        flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.initUI()

    def __del__(self):
        del self.gObj

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
        self.setWindowModality(Qt.ApplicationModal)

    def __centerOnScreen(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def clickedDeck(self, event):
        self.reject()
        strMsg = "{}pickDeck?id={}".format(self.gObj.getServerURL(), self.gObj.getPlayerId())
        # print("draw from deck".format(strMsg))
        self.gObj.receiveResponse(requests.get(strMsg))

    def clickedDiscard(self, event):
        self.reject()
        strMsg = "{}pickDiscard?id={}".format(self.gObj.getServerURL(), self.gObj.getPlayerId())
        # print("draw from discard".format(strMsg))
        self.gObj.receiveResponse(requests.get(strMsg))

class PlayerCheckIn(QDialog):

    def __init__(self):
        super().__init__()
        self.playerURL = QLineEdit(self)
        self.playerName = QLineEdit(self)
        self.gObj = GlobalObject()
        self.initUI()

    def __del__(self):
        del self.gObj

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

        self.gObj.logger.info("playerURL:{} playerID:{} gameURL:{}".format(s, n, self.gObj.gameURL))
        print("playerURL:{} playerID:{} gameURL:{}".format(s, n, self.gObj.gameURL))
        strCheckIn = "{}&name={}".format(s, quote(self.playerName.text()))
        self.gObj.logger.info("PlayerCheckIn:\n{} just checked In".format(strCheckIn))
        # print("DIALOG PlayerCheckIn:\n{} just checked In".format(strCheckIn))
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

class App(QWidget):

    def __init__(self):
        super().__init__()
        self.gObj = GlobalObject()   # communication between dialogs
        self.title = 'Fivecrowns Player UI'
        self.width = 1200
        self.height = 800
        self.handGroupBox = QGroupBox("Player Hand:")
        self.gridHand = QGridLayout()
        self.msgText = QLabel()
        self.cardArray = []
        self.cardIcons = []  # local hand, reordered from server's copy
        self.discardCardIcon = CardDiscardIcon(json.dumps({"suit":0, "value":0}), self)
        self.gObj.addEventListener("dropCard", self.cardMoved)
        self.gObj.addEventListener("playerMessage", self.__playerMessage)
        self.gObj.addEventListener("showDiscard", self.__showDiscard)
        self.gObj.addEventListener("updateHand", self.__playerHand)
        self.gObj.addEventListener("groupcards", self.__groupCards)
        self.flaskApp = Flask(self.title)

        dlg = PlayerCheckIn()  # present at app launch
        if not dlg.exec_():
            pass
            # print("DIALOG: canceled PlayerCheckIn")
        del dlg

        self.initUI()

    def __del__(self):
        del self.flaskApp
        self.flaskApp = None
        del self.cardArray
        del self.cardIcons
        del self.gObj

    def initUI(self):
        self.setWindowTitle(self.title)
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
        self.grpMessage.setStyleSheet("background-color: #BEBEBE;")
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

        self.grpDiscard = QGroupBox()
        self.grpDiscard.setObjectName("grpDiscard")
        self.grpDiscard.setTitle("Discard:")
        discardGrid = QGridLayout()
        discardGrid.addWidget(self.discardCardIcon)
        self.grpDiscard.setLayout(discardGrid)
        self.vrtSubmitDiscard.addWidget(self.grpDiscard)

        # this block was above the block above
        self.btnRefresh = QPushButton()
        self.btnRefresh.setObjectName("btnRefresh")
        self.btnRefresh.setText("Refresh")
        self.btnRefresh.clicked.connect(lambda: self.__playerStatus(self.gObj.getPlayerId()))
        self.vrtSubmitDiscard.addWidget(self.btnRefresh)

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
                            dInner["totscore"] = p["totscore"]
                            dInner["score"] = p["score"]
                            lstOutHand = eval(p["outHand"])
                            grpcnt = 0
                            for card in lstOutHand:
                                if "grpend" in card.keys():
                                    grpcnt += 1
                            dInner["grpcnt"] = grpcnt
                            dInner["outhand"] = lstOutHand
                            lstInner.append(dInner)
                            del lstOutHand
                        dMsg["playerHands"] = lstInner
                    else:
                        dMsg[k] = v
                msg = self.__htmlMessage("roundOver.html", dMsg)
                self.msgText.setText(msg)  # don't move this below the if/then/else tree
                """
                    TODO:  if round == 11, create a file from "msg" which is then pushed to the git hub repo 
                    EOG folder (e.g. ResultsGameEnding202005272103.html).  Note that this file will 
                    need to get the cardimage path references correct.  Only one of these files (each player
                    could potentially send one ... needs to go to the github repo, so you need to think that
                    through (should it be the active dealer for example?)  THe repo needs to be enabled
                    with github pages (github.io) for this to work properly
                """
                if "gameOver" in d.keys():
                    self.btnRefresh.setEnabled(False)  # don't let the user touch this anymore ...
                    dlg = EndGame(self)  # kill it off
                    if not dlg.exec_():
                        pass
                    del dlg

                    strMsg = "{}playerQuit?id={}".format(self.gObj.getServerURL(), self.gObj.getPlayerId())
                    # print("CALL SERVER METHOD: playerQuit\n{}".format(strMsg))
                    jsonResponse = requests.get(strMsg)
                    self.gObj.logger.info("Server Response from playerQuit: {}".format(jsonResponse))

                elif "name" in d.keys() and "dealer" in d.keys():
                    if d["name"] == d["dealer"]:
                        dlg = Dealer()  # present the ability to advance round to the dealer
                        if not dlg.exec_():
                            pass
                        del dlg

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
            syncs player's local hand with the server's hand, retaining the local hand's
            ordering
        """

        if self.gObj.dictResponse:
            serverHand = eval(self.gObj.dictResponse["hand"])
            # print("HAND:\nserver:{} local:{}".format(serverHand, self.cardArray))
            if len(serverHand) > len(self.cardArray):
                inServerNotLocal = list(itertools.filterfalse(lambda i: i in self.cardArray, serverHand))
                self.cardArray.extend(inServerNotLocal)
                # print("inServerNotLocal:{}".format(inServerNotLocal))
            else:
                inLocalNotServer = list(itertools.filterfalse(lambda i: i in serverHand, self.cardArray))
                for card in inLocalNotServer:
                    self.cardArray.remove(card)
                # print("inLocalNotServer:{}".format(inLocalNotServer))

            # now wipe the UI's hand and redraw it based upon the correction above
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
                if i and not (i % 6):   # 6 cards per row max,
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
    def __groupCards(self):
        # TODO: if you wanted a player message indicating that the player is in the process of grouping their cards,
        # you'd need to add another server message here
        dlg = GroupDialog(len(self.gObj.thisPlayer.outhand) - 2, self.gObj.thisPlayer.outhand)   # NEED A WAY TO GET THE ROUND !!!!
        if not dlg.exec_():
            pass
            # print("DIALOG: canceled PlayerDraw")
        del dlg

        strMsg = "{}out?id={}&outhand={}".format(self.gObj.getServerURL(), self.gObj.getPlayerId(), json.dumps(self.gObj.thisPlayer.outhand))
        # print("CALL SERVER METHOD: out\n{}".format(strMsg))
        self.gObj.receiveResponse(requests.get(strMsg))

        # everything below here (and before return) was the __outHand function ...
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
            # you need to sort out dictionary usage before you can switch over
            # template = jinja2.Template(s)
            # s = template.render(dMsg)

        return s

    @QtCore.pyqtSlot()
    def cardMoved(self):
        self.__reorderHand()

        return

    def closeEvent(self, event):
        self.close()

#----*----*----*----*----*----*----*----*----*----*----*----*----*----*----*----*----*----*----*----*

class CardOutIcon(QLabel):

    def __init__(self, item, parent):
        super().__init__(item, parent)
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


class CardDropSpot(QLabel):
    """
        Drop spot for books and runs
    """
    def __init__(self, item, parent):
        super().__init__(item, parent)
        self.parent = parent
        self.setAcceptDrops(True)
        self.d = eval(item)
        imageName = "cardimages/{}_{}.svg".format(self.d["suit"], self.d["value"])
        self.setPixmap(QPixmap(imageName))
        self.show()

    def updateImage(self, item):
        """
            item is json representation of Card()
        """
        self.d = eval(item)
        imageName = "cardimages/{}_{}.svg".format(self.d["suit"],self.d["value"])
        self.setPixmap(QPixmap(imageName))
        self.show()
        return

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if self.parent.isActive:
            pos = event.pos()
            if event.mimeData().hasText():
                text = event.mimeData().text()
                d = eval(text)
                imageName = "cardimages/{}_{}.svg".format(d["suit"], d["value"])
                self.setPixmap(QPixmap(imageName))
                self.show()
                event.acceptProposedAction()

                cardIdx = self.parent.workinghand.index(d)
                self.parent.workinghand.pop(cardIdx)
                self.parent.formOutHand()
                self.parent.nDrops += 1
                if self.parent.nDrops > 2:
                    self.parent.btnAccept.setEnabled(True)
                elif self.parent.nDrops:
                    self.parent.btnReject.setEnabled(True)

class GroupCards(QGroupBox):

    def __init__(self, round, outhand, parent):
        super().__init__(parent)
        self.gObj = GlobalObject()   # communication between dialogs
        self.parent = parent
        self.round = round
        self.outhand = outhand
        self.workinghand = list(outhand)
        self.cardsInGroups = []
        self.gridHand = QGridLayout()
        self.cardIcons = []  # array of cards
        # self.lblScore = QLabel()
        self.isActive = 0  # see GroupType in FiveCrownsGame
        self.nDrops = 0 # count of drops on active book or run
        self.nBooks = 0
        self.nRuns = 0
        self.initUI()

    def initUI(self):
        self.grpDrop = QGroupBox()
        self.grpDrop.setTitle("Drop Cards Here:")
        self.vrtDrop = QVBoxLayout()
        self.cardDropSpot = CardDropSpot(json.dumps({"suit": 0, "value": 0}), self)
        self.vrtDrop.addWidget(self.cardDropSpot)
        self.vrtDrop.addStretch(1)
        self.hrzDrop = QHBoxLayout()
        self.btnAccept = QPushButton()
        self.btnAccept.setText("Accept")
        self.btnAccept.setEnabled(False)
        self.btnAccept.clicked.connect(self.__acceptGroup)
        self.hrzDrop.addWidget(self.btnAccept)
        self.hrzDrop.addStretch(1)
        self.btnReject = QPushButton()
        self.btnReject.setText("Reject")
        self.btnReject.setEnabled(False)
        self.btnReject.clicked.connect(self.__rejectGroup)
        self.hrzDrop.addWidget(self.btnReject)
        self.vrtDrop.addLayout(self.hrzDrop)
        self.grpDrop.setLayout(self.vrtDrop)

        self.grpRun = QGroupBox()
        self.grpRun.setTitle("Run:")
        self.hrzRun = QHBoxLayout()
        self.btnRun = QPushButton()
        self.btnRun.setText("+ Run")
        # self.btnRun.setStyleSheet('QPushButton {background-color: #A3C1DA; color: red;}')
        self.btnRun.clicked.connect(self.__newRun)
        self.hrzRun.addWidget(self.btnRun)
        self.cntRun = QLabel()
        self.cntRun.setText("{}".format(self.nRuns))
        self.hrzRun.addWidget(self.cntRun)
        self.grpRun.setLayout(self.hrzRun)

        self.grpBook = QGroupBox()
        self.grpBook.setTitle("Book:")
        self.hrzBook = QHBoxLayout()
        self.btnBook = QPushButton()
        self.btnBook.setText("+ Book")
        # self.btnBook.setStyleSheet('QPushButton {background-color: #696969; color: yellow;}')
        self.btnBook.clicked.connect(self.__newBook)
        self.hrzBook.addWidget(self.btnBook)
        self.cntBook = QLabel()
        self.cntBook.setText("{}".format(self.nBooks))
        self.hrzBook.addWidget(self.cntBook)
        self.grpBook.setLayout(self.hrzBook)

        self.btnAllDone = QPushButton()
        self.btnAllDone.setText("Score Remaining Cards")
        self.btnAllDone.clicked.connect(self.parent.closeEvent)

        self.grpOutHand = QGroupBox()
        self.grpOutHand.setTitle("Out Hand:")
        self.formOutHand()
        self.grpOutHand.setLayout(self.gridHand)

        self.setTitle("Group Your Cards:")
        grid = QGridLayout()
        grid.addWidget(self.grpBook, 0, 0)
        grid.addWidget(self.grpRun, 1, 0)
        grid.addWidget(self.grpOutHand, 2, 0, 1, 2)
        grid.addWidget(self.btnAllDone, 3, 0, 1, 2)
        grid.addWidget(self.grpDrop, 0, 1, 2, 1)
        self.setLayout(grid)

    def formOutHand(self):
        """
            Get the outhand from the server and pump it into the grid
        """
        # you have to kill off the grid widgets and add them back in using this technique
        self.cardIcons = []

        for i in reversed(range(self.gridHand.count())):
            widgetToRemove = self.gridHand.itemAt(i).widget()
            widgetToRemove.setParent(None)
            widgetToRemove.deleteLater()

        row = 0
        col = 0
        for i, card in enumerate(self.workinghand):
            s = json.dumps(card)
            self.cardIcons.append(CardOutIcon(s, self))
            if i and not (i % 6):  # 6 cards per row max,
                row += 1
                col = 0
            self.gridHand.addWidget(self.cardIcons[i], row, col)  # gotta do something here when i > 7
            col += 1

        return

    def __newBook(self):
        """
            could impact the face of the drop spot
        """
        self.isActive = GroupType.BOOK.value
        self.btnRun.setEnabled(False)
        self.btnBook.setEnabled(False)
        self.btnAllDone.setEnabled(False)
        self.cardDropSpot.updateImage(json.dumps({"suit": 10, "value": 0}))  # new book image
        return

    def __newRun(self):
        """
            could impact the face of the drop spot
        """
        self.isActive = GroupType.RUN.value
        self.btnRun.setEnabled(False)
        self.btnBook.setEnabled(False)
        self.btnAllDone.setEnabled(False)
        self.cardDropSpot.updateImage(json.dumps({"suit": 11, "value": 0})) # new run image
        return

    def __acceptGroup(self):
        """
            increment count of run or books based on isActive
            reset the text of the book or run counter to nRuns / nBooks
            create a new run or book object (server call) based on isActive
            receive response from server which would include the updated score, or
                potentially, the need to reject the group
            enable Run, Book buttons
            disable Accept, Reject buttons
            reset nDrops = 0
        """
        if self.isActive == GroupType.BOOK.value:
            self.nBooks += 1
            self.cntBook.setText("{}".format(self.nBooks))
        else:
            self.nRuns += 1
            self.cntRun.setText("{}".format(self.nRuns))

        self.btnBook.setEnabled(True)
        self.btnRun.setEnabled(True)
        self.btnAccept.setEnabled(False)
        self.btnReject.setEnabled(False)
        self.nDrops = 0

        self.cardDropSpot.updateImage(json.dumps({"suit": 0, "value": 0})) # default image back

        # now determine the cards that are within this group ...
        cardsInCurrentGroup = list(itertools.filterfalse(lambda i: i in self.cardsInGroups, self.outhand))  # remove any other groups first ...
        cardsInCurrentGroup = list(itertools.filterfalse(lambda i: i in self.workinghand, cardsInCurrentGroup))  # ... to determine the currrent group's cards

        strMsg = "{}group?id={}&grpType={}&grpHand={}".format(self.gObj.getServerURL(), self.gObj.getPlayerId(), self.isActive, json.dumps(cardsInCurrentGroup))
        jsonResponse = requests.get(strMsg)
        if jsonResponse:
            dR = eval(jsonResponse.content)

            if "cards" in dR.keys():   # i.e. the group was determined invalid by the server ...
                if self.isActive == GroupType.BOOK.value:
                    self.nBooks -= 1
                    self.cntBook.setText("{}".format(self.nBooks))
                else:
                    self.nRuns -= 1
                    self.cntRun.setText("{}".format(self.nRuns))
                self.__rejectGroup()
            else:
                self.cardsInGroups.extend(cardsInCurrentGroup)
                del cardsInCurrentGroup
                self.isActive = 0
                self.btnAllDone.setEnabled(True)

        # TODO could do an error message here if the jsonResponse was bogus

        return

    def __rejectGroup(self):
        """
            return cards to the hand from this group
            enable Run, Book buttons
            disable Accept, Reject buttons
            could reset the face of the drop spot
            reset nDrops = 0
            We don't need to decrement counts here as the user could
            have rejected before "accepting"
        """
        tempwh = list()
        cardsInCurrentGroup = list(itertools.filterfalse(lambda i: i in self.workinghand, self.outhand))
        self.workinghand.extend(cardsInCurrentGroup)
        for card in self.outhand:
            if card in self.workinghand:
                tempwh.append(card)   # retain the original ordering

        self.workinghand = list(tempwh)
        del tempwh
        self.formOutHand()

        self.btnBook.setEnabled(True)
        self.btnRun.setEnabled(True)
        self.btnAccept.setEnabled(False)
        self.btnReject.setEnabled(False)
        self.btnAllDone.setEnabled(True)
        self.nDrops = 0

        self.cardDropSpot.updateImage(json.dumps({"suit": 0, "value": 0})) # default image back
        del cardsInCurrentGroup
        self.isActive = 0

        return

class GroupDialog(QDialog):

    def __init__(self, round, outhand, flags=Qt.WindowFlags()):
        super().__init__()
        self.title = 'Create BOOKS and RUNS'
        self.width = 600 # 1200
        self.height = 400 # 800
        self.round = round
        self.outhand = outhand
        flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.initUI()

    def __del__(self):
        return

    def closeEvent(self, event):
        self.reject()

    def initUI(self):
        self.resize(self.width, self.height)
        self.__centerOnScreen()

        self.vrtMain = QVBoxLayout()
        self.vrtMain.addWidget(GroupCards(self.round, self.outhand, self))
        self.setLayout(self.vrtMain)

        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle(self.title)

    def __centerOnScreen(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())