import os, sys

class Player():
    def __init__(self, name, uid):
        self.name = name
        self.id = uid  # int id value assigned by server
        # self.isActive = False # assure player took discard action before pass / out
        self.hasExtraCard = False
        self.hasDiscarded = False  # this state changes when player passes
        self.hand = [] # of Card
        self.outhand = [] # of Card, hand after player went out, in their ordering
        self.groups = [] # array of books or runs made by the player, reinitialized after each round
        self.score = []  # one int per round in order by round nbr
        self.totscore = 0 # cumulative total of array score
        self.nbrTimesOut = 0 # cumulative nbr of times this player was the outPlayer
        return

    def __del__(self):
        del self.hand
        del self.outhand
        del self.groups
        del self.score
        del self
        return
