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
        self.books = [] # of Books, reinitialized after each round
        self.runs = [] # of Runs, reinitialized after each round
        self.score = []  # of Int
        return

    def __del__(self):
        del self.hand
        del self.outhand
        del self.score
        del self
        return
