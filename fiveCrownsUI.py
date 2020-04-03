from PyQt5.QtWidgets import (QLabel, QWidget, QPushButton, QDialog, QVBoxLayout, QGridLayout, QGroupBox, QApplication, QLineEdit, QHBoxLayout)
from PyQt5.QtGui import QPixmap, QDrag, QPainter
from PyQt5.QtCore import QMimeData, Qt
from PyQt5 import QtCore
import os, sys, time, functools, json, requests
from urllib.parse import quote
from FiveCrownsGame import Card

# class GameStatus():


@functools.lru_cache()
class GlobalObject(QtCore.QObject):
    """
        using this so my parent window knows a drop happening in the child
    """
    def __init__(self):
        super().__init__()
        self._events = {}

    def addEventListener(self, name, func):
        if name not in self._events:
            self._events[name] = [func]
        else:
            self._events[name].append(func)

    def dispatchEvent(self, name):
        functions = self._events.get(name, [])
        for func in functions:
            QtCore.QTimer.singleShot(0, func)


class PlayerCheckIn(QDialog):

    def __init__(self):
        super().__init__()
        self.playerURL = QLineEdit(self)
        self.playerName = QLineEdit(self)
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

        self.setGeometry(300, 300, 500, 150)
        self.setWindowTitle('Player Check In')
        self.show()

    def __playerCheckIn(self):
        strCheckIn = "{}&name={}".format(self.playerURL.text().strip(), quote(self.playerName.text()))
        print("player just checked In as:{}".format(strCheckIn))
        # response = requests.get(strCheckIn)
        # print(response.content)

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

class App(QDialog):

    def __init__(self):
        super().__init__()
        self.title = 'Fivecrowns Player UI'
        self.left = 10
        self.top = 10
        self.width = 744
        self.height = 562
        GlobalObject().addEventListener("dropCard", self.cardMoved)
        self.cardArray = [{"suit":1,"value":1},{"suit":1,"value":2},{"suit":1,"value":3},{"suit":1,"value":4},{"suit":1,"value":5},{"suit":1,"value":6}]
        self.cardIcons = []
        self.__initHand()
        dlg = PlayerCheckIn()  # present at outset
        if dlg.exec_():   # you need to keep this here as the dialog WAITS ON THIS
            print("success")
        else:
            print("cancel!")  # if we need to figure out if the dialog closed, here's how
        self.initUI()


    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.vrtMain = QVBoxLayout() # self.verticalLayoutWidget)
        self.vrtMain.setContentsMargins(0, 0, 0, 0)
        self.vrtMain.setObjectName("vrtMain")

        self.hzMsgDiscard = QHBoxLayout()
        self.hzMsgDiscard.setObjectName("hzMsgDiscard")

        self.grpMessage = QGroupBox()
        self.grpMessage.setObjectName("grpMessage")
        self.grpMessage.setTitle("Message:")
        self.hzMsgDiscard.addWidget(self.grpMessage, 80)

        self.vrtSubmitDiscard = QVBoxLayout()
        self.vrtSubmitDiscard.setObjectName("vrtSubmitDiscard")
        self.btnRefresh = QPushButton()
        self.btnRefresh.setObjectName("btnRefresh")
        self.btnRefresh.setText("Refresh")
        self.vrtSubmitDiscard.addWidget(self.btnRefresh)
        self.grpDiscard = QGroupBox()
        self.grpDiscard.setObjectName("grpDiscard")
        self.grpDiscard.setTitle("Discard:")
        self.vrtSubmitDiscard.addWidget(self.grpDiscard)
        self.hzMsgDiscard.addLayout(self.vrtSubmitDiscard, 20)
        self.vrtMain.addLayout(self.hzMsgDiscard, 40)

        self.createGridLayout()
        self.vrtMain.addWidget(self.horizontalGroupBox)

        self.setLayout(self.vrtMain)
        self.show()

    def __initHand(self):
        for i in range(0, len(self.cardArray)):
            s = json.dumps(self.cardArray[i])
            self.cardIcons.append(CardIcon(s, self))
        return

    def __reorderHand(self):
        """
            entire local hand is reordered when user drops a card in a new location
        """
        # print("before: {}".format(self.cardArray))
        # print("-------------------")

        for i, card in enumerate(self.cardIcons):
            card = card.exposeCard()
            if card != self.cardArray[i]:
                break

        destIdx = i
        sourceIdx = self.cardArray.index(card)
        # print("destIdx:{} sourceIdx:{} sourceCard:{}".format(destIdx, sourceIdx, card))
        card = self.cardArray.pop(sourceIdx)
        self.cardArray.insert(destIdx, card)

        for i, card in enumerate(self.cardIcons):   # update all cards and local deck
            card.updateImage(json.dumps(self.cardArray[i]))
        # print("after: {}".format(self.cardArray))

        return

    @QtCore.pyqtSlot()
    def cardMoved(self):
        self.__reorderHand()

        return

    def createGridLayout(self):
        self.horizontalGroupBox = QGroupBox("Player Hand:")
        layout = QGridLayout()

        ii = 0
        for i in range(0, 2):  # 2 rows of 3 columns
            for j in range(0, 3):
                layout.addWidget(self.cardIcons[ii], i, j)
                ii += 1

        self.horizontalGroupBox.setLayout(layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())