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

class Encoder(JSONEncoder):
    def default(self, o):
        return o.__dict__

class Game():
    def __init__(self):
        self.Deck = []
        self.__CreateInitialDeck()
        return

    def __del__(self):
        return

    def __CreateInitialDeck(self):
        # create two standard card decks that include 2 jokers but exclude 2s and aces
        for i in range(0, 2):
            self.Deck.append(Card(CardSuit.ONEEYE.value, 0))  # add the two jokers
            self.Deck.append(Card(CardSuit.TWOEYE.value, 0))
            for value in range(3, 14):
                for suit in range(1, 5):
                    self.Deck.append(Card(suit, value))
        return

    def getDeck(self):
        return json.dumps(self.Deck, cls=Encoder)

    def randomCardFromDeck(self):
        if self.Deck != []:
            card = random.choice(self.Deck)
            return json.dumps(card, cls=Encoder)

