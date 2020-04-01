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
    REDJOKER = 5
    BLACKJOKER = 6

class Card():
    def __init__(self, suit, value):
        self.suit = suit
        self.value = value
        return

    def __del__(self):
        del self
        return

    def __eq__(self, other):  # support equivalence testing
        if isinstance(other, Card):
            bools = (self.suit == other.suit)
            boolv = (self.value == other.value)
            if (bools and boolv):
                return True
        return False

    def printCard(self):
        print("suit:{} value:{}".format(self.suit, self.value))
        return

class Encoder(JSONEncoder):
    def default(self, o):
        return o.__dict__

class Game():
    def __init__(self):
        self.players = {} # of Player
        self.playerOrder = [] # dealer ordering
        self.deck = []  # of Card
        self.discard = [] # of Card
        self.dealer = 0
        self.activePlayer = 0
        self.outPlayer = 0
        self.round = 0
        self.checkIns = 0
        self.startGameAfterCheckIns = 0
        self.currentGameStatus = "not active"
        self.__createInitialDeck()

        return

    def __del__(self):
        return

    def __createInitialDeck(self):
        """
            create two standard card decks that include 2 jokers but exclude 2s and aces
        """
        for i in range(0, 2):
            self.deck.append(Card(CardSuit.ONEEYE.value, 0))  # add the two black jokers
            self.deck.append(Card(CardSuit.TWOEYE.value, 0))
            for value in range(3, 14):
                for suit in range(1, 5):  # len CardSuit + 1
                    self.deck.append(Card(suit, value))

        # now shuffle deck and deal initial discard
        random.shuffle(self.deck)
        self.discard.clear()
        self.__moveCardsFromTop(self.deck, self.discard, 1)

        return

    def __moveCardsFromTop(self, s, d, n):
        # presumes [s]ource, [d]estination arguments are [Card]
        for i in range(0, n):
            d.append(s.pop(0))

        return

    def __addPlayer(self):
        # creates a player and adds to Game.players
        newId = random.randint(999, 9999)

        while True:
            newId = random.randint(999, 9999)
            if newId not in self.playerOrder:
                break

        self.playerOrder.append(newId)
        self.players[newId] = Player("__default__", newId)

        return newId

    def __nextPlayer(self, playerId):
        """
            returns Player.id of next player in Game.playerOrder, and accommodates wrapping the array
        """
        nextPlayer = -1   # would be an error if this was returned

        if playerId in self.playerOrder:
            if playerId == self.playerOrder[-1]:
                nextPlayer = self.playerOrder[0]
            else:
                index = self.playerOrder.index(playerId)
                nextPlayer = self.playerOrder[index + 1]

        return nextPlayer

    def __invitePlayer(self, playerEmail, urlOfGame, playerId):
        """
            send an email to "email" containing the URL and checkin endpoint with their ID as a PUT argument
        """
        return

    def __startGame(self):
        """
            Called if we have sufficient checkIns.
            Clean out the players that didn't check in and start the first round
        """
        d = dict(self.players)  # temp used for removing players that didn't check in

        for playerId, player in d.items():
            if player.name == "__default__":
                del self.players[playerId]
                self.playerOrder.remove(playerId)

        del d

        self.__startNextRound()

        return

    def __startNextRound(self):
        """
            starts a new round
        """
        if self.round == 0:
            self.activePlayer = self.__nextPlayer(self.playerOrder[0])  # there must be at least one player to get this far ...
        else:
            self.dealer = self.__nextPlayer(self.dealer)
            self.activePlayer = self.__nextPlayer(self.dealer)
            self.players[self.activePlayer].isActive = True

        self.round += 1   # do we to recognize the end of the game through this method??

        # shuffle full deck, deal first discard, and deal to the players
        self.__createInitialDeck()
        for playerId, player in self.players.items():
            player.hand.clear()
            self.__moveCardsFromTop(self.deck, player.hand, 3 + self.round - 1)

        return

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
        if playerId in self.players.keys():
            player = self.players[playerId]
            if player.name == "__default__":   # conditional will help prevent players from checking in multiple times
                self.players[playerId].name = name
                self.checkIns += 1

        if self.checkIns >= self.startGameAfterCheckIns:
            self.__startGame()  # will start game now given checkIns

        return self.playerGameStatus(playerId)

    def playerGameStatus(self, playerId):
        """
            sends a data bundle back to player with current game status and player's specifics
        """
        d = dict()

        d["round"] = self.round
        d["discard"] = json.dumps(self.discard[-1], cls=Encoder)
        d["checkIns"] = self.checkIns
        d["startGameAfterCheckIns"] = self.startGameAfterCheckIns

        if self.activePlayer:
            d["activePlayer"] = self.players[self.activePlayer].name
            d["nextPlayer"] = self.players[self.__nextPlayer(self.activePlayer)].name

        if self.outPlayer:
            d["outPlayer"] = self.players[self.outPlayer].name

        if playerId in self.players.keys():
            player = self.players[playerId]
            if player:
                d["hand"] = json.dumps(player.hand, cls=Encoder)
                d["score"] = player.score

        return json.dumps(d)

    def pickFromDeck(self, playerId):
        """
            player draws a card from the top of the deck
        """
        if playerId in self.players.keys() and playerId == self.activePlayer:
            player = self.players[playerId]
            if len(player.hand) == (3 + self.round - 1):
                self.__moveCardsFromTop(self.deck, player.hand, 1)

        return self.playerGameStatus(playerId)

    def pickFromDiscard(self, playerId):
        """
            player draws a card from the end of the discard deck
        """
        if playerId in self.players.keys() and playerId == self.activePlayer:
            player = self.players[playerId]
            if len(player.hand) == (3 + self.round - 1):
                player.hand.append(self.discard.pop(-1))  # discard is the last card in discard array

        return self.playerGameStatus(playerId)

    def playerDiscard(self, playerId, cardJSON):
        if playerId in self.players.keys() and playerId == self.activePlayer:
            player = self.players[playerId]
            d = eval(json.loads(cardJSON))
            playerDiscard = Card(d["suit"], d["value"])

            if playerDiscard in player.hand:
                player.hand.remove(playerDiscard)  # doesn't matter if there are multiple playerDiscard cards in hand
                self.discard.append(playerDiscard)
                player.isActive = False

        return self.playerGameStatus(playerId)

    def playerPass(self, playerId):
        if playerId in self.players.keys() and playerId == self.activePlayer:
            player = self.players[playerId]
            print(player.isActive)
            if len(player.hand) == (3 + self.round - 1) and not player.isActive:
                self.activePlayer = self.__nextPlayer(self.activePlayer)

        return self.playerGameStatus(playerId)

    def playerOut(self, playerId, outCards):
        if playerId in self.players.keys() and playerId == self.activePlayer:
            # need some form of validation here !!!
            # thinking of a structure like this:
            # {"out":, "runs": [{cards ...}, {cards ...}], "books": [{cards ...}, {cards ...}]}
            player = self.players[playerId]
            if len(player.hand) == (3 + self.round - 1) and not player.isActive:
                self.outPlayer = playerId
                """
                    need to do something here to determine when the next player
                    is once again the outPlayer, as that would end the round.
                    Additionally, once round > 11 we end the game.  Should
                    email round scores to everyone after game.  Need to write
                    clear rules for the client in terms of "out" e.g. once outPlayer 
                    is set, then "pass" is no longer enabled on the client, only "out"
                """
                self.activePlayer = self.__nextPlayer(self.activePlayer)
                # set player's score for this round to 0

        return self.playerGameStatus(playerId)

    def peakIds(self):
        """
            peak at the playerIds - debugging method
        """

        return json.dumps(self.playerOrder)


    # def getDeck(self):
    #     return json.dumps(self.deck, cls=Encoder)
    #
    # def randomCardFromDeck(self):
    #     if self.deck:
    #         card = random.choice(self.deck)
    #         return json.dumps(card, cls=Encoder)
    #
    # def showDiscard(self):
    #     if self.discard:
    #         return json.dumps(self.discard[-1], cls=Encoder)
    #


