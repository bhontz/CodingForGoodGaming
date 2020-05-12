import os, sys, itertools, json, random, time
from enum import Enum
from json import JSONEncoder
from FiveCrownsPlayer import Player

class GroupType(Enum):
    BOOK = 1
    RUN = 2

class CardSuit(Enum):
    CLUB  = 1
    DIAMOND = 2
    HEART = 3
    SPADE = 4
    STAR = 5
    REDJOKER = 6
    BLACKJOKER = 7

class Card():
    def __init__(self, deck, suit, value):
        self.deck = deck    # found I needed this to ID card duplication
        self.suit = suit
        self.value = value
        return

    def __del__(self):
        del self
        return

    def __eq__(self, other):  # support equivalence testing for Card comparisons
        if isinstance(other, Card):
            bools = (self.suit == other.suit)
            boolv = (self.value == other.value)
            if (bools and boolv):
                return True
        return False

    def printCard(self):
        # self.log("deck:{} suit:{} value:{}".format(self.deck, self.suit, self.value))
        print("deck:{} suit:{} value:{}".format(self.deck, self.suit, self.value))
        return

class GroupCards():
    def __init__(self, round, type, cards):
        self.round = round
        self.type = type
        self.cards = eval(cards.rstrip('\n')) # array of validated cards TODO: HAD AN \n error once????
        self.notwild = [] # array of working cards
        self.wildCards = 0
        self.suit = 0
        self.value = 0
        self.isValid = True   # external methods test this to see if the group is valid
        self.__addCards()
        return

    def __del__(self):
        del self.notwild
        del self.cards
        return

    def __addCards(self):
        """
            validates the run or book by setting class parameter isValid == True
        """
        if len(self.cards) < 3:   # UI should have already have checked this, but ...
            return json.dumps(self.cards)

        for card in self.cards:
            if card["value"] == 0 or (card["value"] == (self.round + 2)):
                self.wildCards += 1
            else:
                self.notwild.append(card)
                if self.type == GroupType.BOOK.value:
                    if not self.value:
                        self.value = card["value"]
                    elif self.value != card["value"]:
                        self.isValid = False
                        break

                elif self.type == GroupType.RUN.value:
                    if not self.suit:
                        self.suit = card["suit"]
                    elif self.suit != card["suit"]:
                        self.isValid = False
                        break

        # additional validation required in for RUNS ...
        if self.isValid and (self.type == GroupType.RUN.value):
            gaps = 0
            n = len(self.notwild)
            if n > 1:
                self.notwild = sorted(self.notwild, key=lambda k: k["value"])

                for i in range(1, n):
                    gaps += (self.notwild[i]["value"] - self.notwild[i-1]["value"] - 1)

                if gaps and self.wildCards < gaps:  # make sure the wildcards fill the gaps between the values
                    self.isValid = False

        return


class Encoder(JSONEncoder):
    def default(self, o):
        return o.__dict__

class Game():
    def __init__(self):
        self.startDateTime = time.localtime()
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
        self.roundOver = 0
        self.gameOver = 0
        self.URL = None
        return

    def __del__(self):
        del self.players
        del self.playerOrder
        del self.deck
        del self.discard
        return

    def log(self, msg):  # simple wrapper for logging to stdout on heroku
        try:
            if type(msg) is dict:
                msg = json.dumps(msg)
            sys.stdout.write(u"\t--fc-->{}: {}\n".format(time.strftime("%H:%M:%S", time.localtime()), msg))
        except UnicodeEncodeError:
            pass  # squash logging errors in case of non-ascii text
        sys.stdout.flush()

        return

    def setURL(self, url):
        self.URL = url
        return

    def __wipeOut(self):
        self.players.clear()
        del self.players
        self.players = None
        self.playerOrder.clear()
        del self.playerOrder
        self.playerOrder = None
        self.deck.clear()
        del self.deck
        self.deck = None
        self.discard.clear()
        del self.discard
        self.discard = None

        self.players = {}  # of Player
        self.playerOrder = []  # dealer ordering
        self.deck = []  # of Card
        self.discard = []  # of Card
        self.dealer = 0
        self.activePlayer = 0
        self.outPlayer = 0
        self.round = 0
        self.checkIns = 0
        self.startGameAfterCheckIns = 0
        self.roundOver = 0
        self.gameOver = 0
        return

    def createGame(self, lstEmails, checkIns):
        """
            create the new players listed players and assign their id.
            send players an email with their URL endpoint for check-in.
            game loop starts when the Game.checkIns == startAfterCheckIns.
            (note: "un-deal" players that did not check in and then delete these players at Game Start)
        """
        self.__createInitialDeck()  # moved here from __init__
        self.startDateTime = time.localtime()
        dMsg = {"message": "New Game Started at: {}  Invited {} players by email.  Waiting for {} players to check in".format(time.strftime("%H:%M:%S", self.startDateTime), len(lstEmails), checkIns)}

        if not checkIns or checkIns > len(lstEmails):
            checkIns = len(lstEmails)

        self.startGameAfterCheckIns = checkIns

        for p in lstEmails:
            self.__addPlayer()

        # for p in lstEmails:   # this role might be better suited for a separate "launch the game server" app
        #     playerId = self.__addPlayer()   # you still need this though ...
        #     # self.__invitePlayer(p, "http://localhost:5000", playerId)

        return json.dumps(dMsg)

    def __createInitialDeck(self):
        """
            create two standard card decks that include 2 jokers but exclude 2s and aces
        """
        self.deck.clear()
        for deckId in range(0, 2):  # two decks
            self.deck.append(Card(deckId, CardSuit.REDJOKER.value, 0))  # add the jokers
            self.deck.append(Card(deckId, CardSuit.BLACKJOKER.value, 0))
            for value in range(3, 14):
                for suit in range(1, 6):  # len CardSuit + 1
                    self.deck.append(Card(deckId, suit, value))
        """
            4/17/20 - when I added the star suit to the deck, I noted there were really SIX
            jokers within the actual fivecrowns playing deck, so adding two more below!
            Also incrementing deckId from loop above to accommodate star suit ...
        """
        self.deck.append(Card(2, CardSuit.REDJOKER.value, 0))  # add the two extra jokers
        self.deck.append(Card(2, CardSuit.BLACKJOKER.value, 0))

        # now shuffle deck and deal initial discard
        for i in range(0, random.randint(1, 7)):  # i wasn't happy with the shuffle in practice
            random.shuffle(self.deck)
        self.discard.clear()
        self.__moveCardsFromTop(self.deck, self.discard, 1)

        return

    def __moveCardsFromTop(self, s, d, n):
        # presumes [s]ource, [d]estination arguments are [Card], n = nbr Cards
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

    def __makeUniqueName(self, name):
        """
            amends player provided name if it is already used
        """
        lstNames = []

        for player in self.players.values():
            lstNames.append(player.name)

        while name in lstNames:
            name = "Another " + name

        return name

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

    # def __invitePlayer(self, playerEmail, urlOfGame, playerId):
    #     """
    #         send an email to "email" containing the URL and checkin endpoint with their ID as a PUT argument
    #         TODO: this role might be better suited for a seperate game launching app
    #     """
    #     return

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

        self.gameOn = 1
        self.dealer = self.playerOrder[0]
        self.activePlayer = self.__nextPlayer(self.dealer)

        self.startNextRound(self.dealer)

        return

    def __scoreHand(self, playerId):
        """
            called at the end of each round, updates the player.score array
        """
        if playerId in self.players.keys():
            player = self.players[playerId]
            groupedCards = list()
            for group in player.groups:
                groupedCards.extend(group.cards)

            # if the outhand is equal to the groupedCards, then the score is 0
            cardsToScore = []
            if len(player.outhand) > len(groupedCards):
                cardsToScore = list(itertools.filterfalse(lambda i: i in groupedCards, player.outhand))

            print("SCORING CARDS:\n groupedCards:{} cardsToScore:{}".format(groupedCards, cardsToScore))

            score = 0
            for card in cardsToScore:
                if card["value"] > 10:
                    score += 10
                elif card["value"] == 0:  # ungrouped joker, in this case we're counting them as 15
                    score += 15
                else:
                    score += card["value"]   # would also hold true for an ungrouped round nbr wildcard

            if len(player.score) < self.round:
                player.score.append(score)   # I think we could safely call only this particular line here ...
            else:
                player.score[self.round] = score

            player.totscore += score

        return

    def __arrangeOuthand(self, playerId):
        """
            after the player is out and the hand scored, arrange the outhand in a group ordering
            and "tag" the end of each group hand to facilitate displaying the outhand in groups
        """
        if playerId in self.players.keys():
            nOutHand = list()
            player = self.players[playerId]

            for grp in player.groups:
                for card in grp.cards:
                    nOutHand.append(card)
                    player.outhand.pop(player.outhand.index(card))
                card = nOutHand[-1]
                card["grpend"] = 1

            nOutHand.extend(player.outhand)
            player.outhand = nOutHand
            del nOutHand

        return

    def __winningPlayerName(self):
        """
            called at 'GAME OVER' returns the name of the winning player
        """
        winningScore = 9999
        winningName = ""

        for player in self.players.values():
            if player.totscore < winningScore:
                winningScore = player.totscore
                winningName = player.name

        return winningName

    def startNextRound(self, dealerId):
        """
            starts a new round
        """
        if self.players[dealerId] == self.players[self.dealer]:  # only the dealer can call this method
            self.roundOver = 0
            self.outPlayer = 0
            self.activePlayer = self.__nextPlayer(dealerId)  # added after Easter evening game

            self.round += 1

            # shuffle full deck, deal first discard, and deal to the players
            self.__createInitialDeck()
            for playerId, player in self.players.items():
                player.hand.clear()
                player.outhand.clear()   #  5/12/2020
                player.groups.clear()
                player.hasExtraCard = False
                player.hasDiscarded = False
                self.__moveCardsFromTop(self.deck, player.hand, 2 + self.round)

        return self.playerGameStatus(dealerId)

    def playerCheckIn(self, playerId, name):
        """
            player executes this indicating they're ready to play
            increments Game.checkIns and assigns name player provides to Game.Player[playerId]
        """
        if playerId in self.players.keys():
            player = self.players[playerId]
            if player.name == "__default__":   # conditional will help prevent players from checking in multiple times
                self.players[playerId].name = self.__makeUniqueName(name)
                self.checkIns += 1

        if self.checkIns >= self.startGameAfterCheckIns:
            self.__startGame()  # will start game now given checkIns

        return self.playerGameStatus(playerId)

    def pickFromDeck(self, playerId):
        """
            player draws a card from the top of the deck
        """
        if playerId in self.players.keys() and playerId == self.activePlayer:
            player = self.players[playerId]
            if len(player.hand) == (2 + self.round):
                self.__moveCardsFromTop(self.deck, player.hand, 1)
                player.hasExtraCard = True

        return self.playerGameStatus(playerId)

    def pickFromDiscard(self, playerId):
        """
            player draws a card from the end of the discard deck
        """
        if playerId in self.players.keys() and playerId == self.activePlayer:
            player = self.players[playerId]
            if len(player.hand) == (2 + self.round):
                player.hand.append(self.discard.pop(-1))  # discard is the last card in discard array
                player.hasExtraCard = True

            if not self.discard:   # this can happen if the only card is drawn
                self.__moveCardsFromTop(self.deck, self.discard, 1)

        return self.playerGameStatus(playerId)

    def playerDiscard(self, playerId, cardJSON):
        if playerId in self.players.keys() and playerId == self.activePlayer:
            player = self.players[playerId]
            d = eval(json.loads(cardJSON))
            playerDiscard = Card(d["deck"], d["suit"], d["value"])

            if playerDiscard in player.hand and len(player.hand) > (2 + self.round):
                player.hand.remove(playerDiscard)  # doesn't matter if there are multiple playerDiscard cards in hand
                self.discard.append(playerDiscard)
                player.hasExtraCard = False
                player.hasDiscarded = True

        return self.playerGameStatus(playerId)

    def playerPass(self, playerId):
        if playerId in self.players.keys() and playerId == self.activePlayer:
            player = self.players[playerId]
            if len(player.hand) == (2 + self.round) and player.hasDiscarded == True:
                self.activePlayer = self.__nextPlayer(self.activePlayer)
                player.hasDiscarded = False

        return self.playerGameStatus(playerId)

    def playerOut(self, playerId, outHand):
        if playerId in self.players.keys() and playerId == self.activePlayer:
            player = self.players[playerId]
            if len(player.hand) == (2 + self.round) and player.hasDiscarded == True:
                if not self.outPlayer:   # outPlayer is the first one out
                    self.outPlayer = playerId

                player.hasDiscarded = False  # reset
                player.outhand = eval(outHand)  # this is the players hand in their ordering when then went out

                self.__scoreHand(playerId)  # updates player.score[self.round]
                # print("PLAYER OUT - playerId:{} round:{} score:{}".format(playerId, self.round, player.score[self.round-1]))
                self.__arrangeOuthand(playerId)  # set ups player.outhand for display purposes

                player.hand.clear()
                # self.log("Player's OUTHAND\n{}: ".format(player.outhand))

                self.activePlayer = self.__nextPlayer(self.activePlayer)

                if self.activePlayer == self.outPlayer:  # start a new round!
                    self.roundOver = 1
                    if self.round == 11:  # Game ending value
                        self.gameOver = 1
                    else:
                        self.log("START OF ROUND:{}".format(self.round + 1))
                        self.dealer = self.__nextPlayer(self.dealer)  # need to set the dealer before the next round starts

        return self.playerGameStatus(playerId)

    def playerAddGroup(self, playerId, grpType, grpHand):
        """
            player has just created a run or a book which needs to be validated, and if valid
            it's then added to the player structure, otherwise the hand is returned
        """
        # print("FROM FC - playerId:{} grpType:{} grpHand:{}".format(playerId, grpType, grpHand))
        if playerId in self.players.keys() and playerId == self.activePlayer:
            player = self.players[playerId]
            group = GroupCards(self.round, grpType, grpHand)
            if group.isValid == True:
                player.groups.append(group)
                return json.dumps(dict(playerId=playerId, round=self.round))
            else:
                return json.dumps(dict(playerId=playerId, round=self.round, cards=grpHand))


    def playerGameStatus(self, playerId):
        """
            sends a data bundle back to player with current game status and player's specifics
        """
        d = dict()

        if self.roundOver == 1:
            d["roundOver"] = self.roundOver
            if self.gameOver == 1:
                d["gameOver"] = self.gameOver
                d["winner"] = self.__winningPlayerName()
            d["name"] = self.players[playerId].name
            d["round"] = self.round
            d["outPlayer"] = self.players[self.outPlayer].name
            d["dealer"] = self.players[self.dealer].name
            lstPlayers = list()
            for playerId in self.playerOrder:
                player = self.players[playerId]
                dPlayer = dict(name=player.name, score=player.score[self.round-1], totscore=player.totscore, outHand=json.dumps(player.outhand))
                lstPlayers.append(dPlayer)
            d["playerHands"] = json.dumps(lstPlayers)
            d["discard"] = json.dumps(dict(suit=0, value=0), cls=Encoder)

        else:

            d["id"] = playerId
            d["name"] = self.players[playerId].name
            d["round"] = self.round
            d["discard"] = json.dumps(self.discard[-1], cls=Encoder)
            d["checkIns"] = self.checkIns
            d["startGameAfterCheckIns"] = self.startGameAfterCheckIns

            if self.activePlayer:
                d["activePlayer"] = self.players[self.activePlayer].name
                d["nextPlayer"] = self.players[self.__nextPlayer(self.activePlayer)].name
                if not self.players[self.activePlayer].hasExtraCard:
                    d["hasExtraCard"] = 0  # can't pass true, false as JSON
                else:
                    d["hasExtraCard"] = 1
                if not self.players[self.activePlayer].hasDiscarded:
                    d["hasDiscarded"] = 0
                else:
                    d["hasDiscarded"] = 1

            if self.outPlayer:
                d["outPlayer"] = self.players[self.outPlayer].name

            if playerId in self.players.keys():
                player = self.players[playerId]
                if player:
                    d["hand"] = json.dumps(player.hand, cls=Encoder)
                    # d["score"] = player.score

        return json.dumps(d)

    def endGame(self):
        s = "Ending Game Started: {}".format(time.strftime("%H:%M:%S", self.startDateTime))
        self.__wipeOut()

        return json.dumps(s)

    def peakIds(self):
        """
            peak at the playerIds - debugging method
        """

        return json.dumps(self.playerOrder)


