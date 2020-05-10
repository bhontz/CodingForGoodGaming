from PyQt5.QtWidgets import (QLabel, QScrollArea, QDesktopWidget, QPushButton, QDialog, QVBoxLayout, QGridLayout, QGroupBox, QApplication, QLineEdit, QHBoxLayout)
from PyQt5.QtGui import QPixmap, QDrag, QPainter
from PyQt5.QtCore import QMimeData, Qt, QSize
from PyQt5 import QtCore
import os, sys, time, itertools, functools, json, requests
from urllib.parse import quote
from flask import Flask, render_template_string
from FiveCrownsPlayer import Player

exampleOutHand = [{"deck": 1, "suit": 3, "value": 8}, {"deck": 1, "suit": 3, "value": 7}, {"deck": 0, "suit": 1, "value": 4}, {"deck": 0, "suit": 6, "value": 0},\
{"deck": 2, "suit": 3, "value": 8}, {"deck": 1, "suit": 1, "value": 4}, {"deck": 0, "suit": 3, "value": 13}, {"deck": 1, "suit": 4, "value": 10},\
{"deck": 1, "suit": 4, "value": 2}, {"deck": 1, "suit": 2, "value": 12}, {"deck": 0, "suit": 3, "value": 3}, {"deck": 0, "suit": 2, "value":9}, \
{"deck": 1, "suit": 1, "value": 6}]

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

    # def dragEnterEvent(self, event):
    #     print("dragEnterEvent - pos: {}".format(event.pos()))
    #     if event.mimeData().hasText():
    #         event.acceptProposedAction()

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
        self.parent = parent
        self.round = round
        self.outhand = outhand
        self.workinghand = list(outhand)
        self.gridHand = QGridLayout()
        self.cardIcons = []  # array of cards
        self.lblScore = QLabel()
        self.isActive = 0  # 1 = Book is active, 2 = Run is active
        self.nDrops = 0 # count of drops on active book or run
        self.nBooks = 0
        self.nRuns = 0
        self.initUI()

    def initUI(self):
        self.grpDrop = QGroupBox()
        self.grpDrop.setTitle("Drop Cards Here:")
        self.vrtDrop = QVBoxLayout()
        self.scoreOutHand()
        self.vrtDrop.addWidget(self.lblScore)
        self.vrtDrop.addStretch(1)
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

    def scoreOutHand(self):
        """
        """
        score = 0

        for card in self.workinghand:
            if not (card["value"] == 0 or card["value"] == (self.round + 2)):
                if card["value"] > 10:
                    score += 10
                else:
                    score += card["value"]

        self.lblScore.setText("Score: {}".format(score))

        return

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
        self.isActive = 1  # BOOK is active
        self.btnRun.setEnabled(False)
        self.btnBook.setEnabled(False)
        self.cardDropSpot.updateImage(json.dumps({"suit": 10, "value": 0}))  # new book image
        return

    def __newRun(self):
        """
            could impact the face of the drop spot
        """
        self.isActive = 2  # RUN is active
        self.btnRun.setEnabled(False)
        self.btnBook.setEnabled(False)
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
        if self.isActive == 1:   # BOOK
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
        self.scoreOutHand()

        self.cardDropSpot.updateImage(json.dumps({"suit": 0, "value": 0})) # default image back
        return

    def __rejectGroup(self):
        """
            return cards to the hand from this group
            enable Run, Book buttons
            disable Accept, Reject buttons
            could reset the face of the drop spot
            reset nDrops = 0
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
        self.nDrops = 0

        self.cardDropSpot.updateImage(json.dumps({"suit": 0, "value": 0})) # default image back
        return

class GroupDialog(QDialog):

    def __init__(self, flags=Qt.WindowFlags()): #  flags=Qt.WindowFlags()
        super().__init__()
        self.title = 'Fivecrowns Player UI'
        self.width = 600 # 1200
        self.height = 400 # 800
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
        self.vrtMain.addWidget(GroupCards(len(exampleOutHand) - 2, exampleOutHand, self))
        self.setLayout(self.vrtMain)

        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle(self.title)
        self.show()

    def __centerOnScreen(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = GroupDialog()
    sys.exit(app.exec_())