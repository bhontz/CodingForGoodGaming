from fc import CardIcon
from PyQt5.QtWidgets import (QLabel, QScrollArea, QDesktopWidget, QPushButton, QDialog, QVBoxLayout, QGridLayout, QGroupBox, QApplication, QLineEdit, QHBoxLayout)
from PyQt5.QtGui import QPixmap, QDrag, QPainter
from PyQt5.QtCore import QMimeData, Qt, QSize
from PyQt5 import QtCore
import os, sys, time, itertools, functools, json, requests
from urllib.parse import quote
from flask import Flask, render_template_string
from FiveCrownsPlayer import Player

exampleOutHand = [{"deck": 1, "suit": 3, "value": 8}, {"deck": 1, "suit": 3, "value": 7}, {"deck": 0, "suit": 1, "value": 4}, {"deck": 0, "suit": 6, "value": 0}]

class CardOutIcon(CardIcon):
    def __init__(self, item, parent):
        super().__init__(item, parent)
        self.setAcceptDrops(False)
        self.show()

    def dropEvent(self, event):
        return

class CardDropSpot(QLabel):
    """
        Drop spot for books and runs
    """
    def __init__(self, item, parent):
        super().__init__(item, parent)
        self.setAcceptDrops(True)
        self.d = eval(item)
        imageName = "cardimages/{}_{}.svg".format(self.d["suit"], self.d["value"])
        self.setPixmap(QPixmap(imageName))
        self.show()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        print("i'm trying to drop my load!!")
        pos = event.pos()
        if event.mimeData().hasText():
            text = event.mimeData().text()
            d = eval(text)
            imageName = "cardimages/{}_{}.svg".format(d["suit"], d["value"])
            print("imagename: {}".format(imageName))
            self.setPixmap(QPixmap(imageName))
            self.show()
            event.acceptProposedAction()

class GroupCards(QGroupBox):
    def __init__(self, parent):
        super().__init__(parent)
        self.cardIcons = []  # array of cards
        self.gridHand = QGridLayout()
        self.initUI()

    def initUI(self):
        self.grpDrop = QGroupBox()
        self.grpDrop.setTitle("Drop Cards Here:")
        self.vrtDrop = QVBoxLayout()
        self.lblGroup = QLabel()
        self.lblGroup.setText("Run #1")
        self.vrtDrop.addWidget(self.lblGroup)
        self.vrtDrop.addStretch(1)
        # self.lblDropSpot = QLabel()
        # self.lblDropSpot.setPixmap(QPixmap("cardimages/{}_{}.svg".format(0, 0)))
        # self.vrtDrop.addWidget(self.lblDropSpot)
        self.vrtDrop.addWidget(CardDropSpot(json.dumps({"suit": 0, "value": 0}), self))
        self.vrtDrop.addStretch(1)
        self.hrzDrop = QHBoxLayout()
        self.btnAccept = QPushButton()
        self.btnAccept.setText("Accept")
        self.hrzDrop.addWidget(self.btnAccept)
        self.hrzDrop.addStretch(1)
        self.btnReject = QPushButton()
        self.btnReject.setText("Reject")
        self.hrzDrop.addWidget(self.btnReject)
        self.vrtDrop.addLayout(self.hrzDrop)
        self.grpDrop.setLayout(self.vrtDrop)

        self.grpRun = QGroupBox()
        self.grpRun.setTitle("Run:")
        self.hrzRun = QHBoxLayout()
        self.btnRun = QPushButton()
        self.btnRun.setText("+ Run")
        self.hrzRun.addWidget(self.btnRun)
        self.cntRun = QLabel()
        self.cntRun.setText("2")
        self.hrzRun.addWidget(self.cntRun)
        self.grpRun.setLayout(self.hrzRun)

        self.grpBook = QGroupBox()
        self.grpBook.setTitle("Book:")
        self.hrzBook = QHBoxLayout()
        self.btnBook = QPushButton()
        self.btnBook.setText("+ Book")
        self.hrzBook.addWidget(self.btnBook)
        self.cntBook = QLabel()
        self.cntBook.setText("0")
        self.hrzBook.addWidget(self.cntBook)
        self.grpBook.setLayout(self.hrzBook)

        self.btnAllDone = QPushButton()
        self.btnAllDone.setText("All Done")

        self.grpOutHand = QGroupBox()
        self.grpOutHand.setTitle("Out Hand:")
        self.__formOutHand()
        self.grpOutHand.setLayout(self.gridHand)

        self.setTitle("Group Your Cards:")
        grid = QGridLayout()
        grid.addWidget(self.grpBook, 0, 0)
        grid.addWidget(self.grpRun, 1, 0)
        grid.addWidget(self.grpOutHand, 2, 0, 1, 2)
        grid.addWidget(self.btnAllDone, 3, 0, 1, 2)
        grid.addWidget(self.grpDrop, 0, 1, 2, 1)
        self.setLayout(grid)

    def __formOutHand(self):
        """
            Get the outhand from the server and pump it into the grid
        """
        row = 0
        col = 0
        for i, card in enumerate(exampleOutHand):
            s = json.dumps(card)
            self.cardIcons.append(CardOutIcon(s, self))
            if i and not (i % 4):  # 4 cards per row max,
                row += 1
                col = 0
            self.gridHand.addWidget(self.cardIcons[i], row, col)  # gotta do something here when i > 7
            col += 1

        return

class App(QDialog):

    def __init__(self):
        super().__init__()
        self.title = 'Fivecrowns Player UI'
        self.width = 600 # 1200
        self.height = 400 # 800

        self.initUI()

    def __del__(self):
        return

    def initUI(self):
        self.setWindowTitle(self.title)
        self.resize(self.width, self.height)
        self.__centerOnScreen()

        self.vrtMain = QVBoxLayout()
        self.vrtMain.addWidget(GroupCards(self))
        self.setLayout(self.vrtMain)
        self.show()

    def __centerOnScreen(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())