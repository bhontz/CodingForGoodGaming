import os, sys, requests, json, random, time
from enum import Enum
from json import JSONEncoder
from datetime import datetime
from FiveCrownsPlayer import *

class CardSuit(Enum):
    CLUB  = 1
    DIAMOND = 2
    HEART = 3
    SPADE = 4
    ONEEYE = 5
    TWOEYE = 6

class Card():
    def __init__(self, suit, value):
        self.suit = suit
        self.value = value
        return

    def __del__(self):
        del self
        return

class Encoder(JSONEncoder):
    def default(self, o):
        return o.__dict__

class Game():
    def __init__(self):
        self.players = [] # of Player
        self.deck = []  # of Card
        self.discard = [] # of Card
        self.dealer = 0
        self.activePlayer = 0
        self.outPlayer = -1
        self.round = 0
        self.checkIns = 0
        self.startGameAfterCheckIns = 0
        self.currentGameStatus = "not active"
        self.__createInitialDeck()

        return

    def __del__(self):
        return

    def __createInitialDeck(self):
        # create two standard card decks that include 2 jokers but exclude 2s and aces
        for i in range(0, 2):
            self.deck.append(Card(CardSuit.ONEEYE.value, 0))  # add the two jokers
            self.deck.append(Card(CardSuit.TWOEYE.value, 0))
            for value in range(3, 14):
                for suit in range(1, 5):
                    self.deck.append(Card(suit, value))

        # now shuffle deck and deal initial discard
        random.shuffle(self.deck)
        self.__moveCardsFromTop(self.deck, self.discard, 1)

        return

    def __moveCardsFromTop(self, s, d, n):
        # presumes [s]ource, [d]estination arguments are [Card]
        for i in range(0, n):
            d.append(s.pop(0))

        return
    def __addPlayer(self):
        # creates a player and adds to Game.players
        if not self.players:
            newId = 0
        else:
            newId = len(self.players) - 1    # should make this at least a random nbr out of 1000

        self.players.append(Player("__default__", newId))  # players add their own name at check-in

        return newId

    def __invitePlayer(self, email, url, id):
        """
            send an email to "email" containing the URL and checkin endpoint with their ID as a PUT argument
        """
        return

    def __startGame(self):
        """
            If we have the checkIns, start the game up with housekeeping handled first
        """
        if self.checkIns >= self.startGameAfterCheckIns:
            finalplayers = [player for player in self.players if player.name != "__default__"]
            self.players = finalplayers
            del finalplayers  # now your ids r screwed



    def createGame(self, lstEmails, checkIns):
        """
            create the new players listed players and assign their id.
            send players an email with their URL endpoint for check-in.
            game loop starts when the Game.checkIns == startAfterCheckIns.
            (note: "un-deal" players that did not check in and then delete these players at Game Start)
        """
        d = {"message": "New Game Started.  Inviting {} players by email.  Waiting for {} players to check in".format(len(lstEmails), checkIns)}

        if not checkIns or checkIns > len(lstEmails):
            checkIns = len(lstEmails)

        self.startGameAfterCheckIns = checkIns

        for p in lstEmails:
            playerId = self.__addPlayer()
            # self.__invitePlayer(p, "http://localhost:5000", playerId)

        return json.dumps(d)



    def playerCheckIn(self, playerId, name):
        """
            player executes this indicating they're ready to play
            increments Game.checkIns and assigns name player provides to Game.Player[playerId]
        """

        if playerId != -1:
            player = self.players[playerId]
            if player.name == "__default__":   # conditional will help prevent players from checking in multiple times
                self.players[playerId].name = name
                self.checkIns += 1

        self.__startGame()  # will start game now given checkIns

        return self.__playerGameStatus(playerId)


    def __playerGameStatus(self, playerId):
        """
            sends a data bundle back to player with current game status and player's specifics
        """
        d = {"message": "an error has occurred"}

        player = self.players[playerId]
        if player:
            d["round"] = self.round
            d["discard"] = self.discard
            d["hand"] = player.hand
            d["score"] = player.score
            d["message"] = self.currentGameStatus

        return json.dumps(d)


    def dealToPlayers(self):
        # shuffles cards, deals[MOVES] the appropriate number given the round to the players
        self.round = 1  # debug, this will[might] get separately
        random.shuffle(self.deck)
        for player in self.players:
            player.hand.clear()
            self.__moveCardsFromTop(self.deck, player.hand, 3 + self.round - 1)

        return json.dumps(self.players[0].hand, cls=Encoder)   # this is just a debugger for now

    def getDeck(self):
        return json.dumps(self.deck, cls=Encoder)

    def randomCardFromDeck(self):
        if self.deck:
            card = random.choice(self.deck)
            return json.dumps(card, cls=Encoder)

    def showDiscard(self):
        if self.discard:
            return json.dumps(self.discard[-1], cls=Encoder)



