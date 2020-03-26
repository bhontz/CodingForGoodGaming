import os, sys, requests, json, random
from enum import Enum
from json import JSONEncoder
from datetime import datetime

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

class Player():
    def __init__(self, name, uid):
        self.name = name
        self.id = uid  # int value assigned by server
        self.hand = [] # of Card
        self.score = []  # of Int
        return

    def __del__(self):
        del self.hand
        del self.score
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
        # presumes arguments are [Card]
        for i in range(0, n):
            d.append(s.pop(0))

        return

    def addPlayer(self, name):
        # creates a player and adds to Game.players
        if not self.players:
            newId = 0
        else:
            newId = len(self.players) - 1

        self.players.append(Player(name, newId))

        return json.dumps("added player: {}".format(name))

    def dealToPlayers(self):
        # shuffles cards, deals[MOVES] the appropriate number given the round to the players
        self.round = 1  # debug, this will[might] get separately
        random.shuffle(self.deck)
        for player in self.players:
            player.hand.clear()
            self.__moveCardsFromTop(self.deck, player.hand, 3 + self.round - 1)

        return json.dumps(self.players[0].hand, cls=Encoder)   # this is just a debugger for now

    # def shuffleDeck(self):
    #     # NOTE this will be combined with DEAL, as can't think of another
    #     # application for this when DEAL isn't involved.
    #     random.shuffle(self.deck)
    #     return json.dumps(self.deck, cls=Encoder)

    def getDeck(self):
        return json.dumps(self.deck, cls=Encoder)

    def randomCardFromDeck(self):
        if self.deck:
            card = random.choice(self.deck)
            return json.dumps(card, cls=Encoder)

    def showDiscard(self):
        if self.discard:
            return json.dumps(self.discard[-1], cls=Encoder)



