import os, sys, requests, json, random, time
from enum import Enum
from json import JSONEncoder
from datetime import datetime
from FiveCrownsGame import *

class Player():
    def __init__(self, name, uid):
        self.name = name
        self.id = 0  # int id value assigned by server
        self.isActive = False # assure player took discard action before pass / out
        self.hand = [] # of Card
        self.score = []  # of Int
        return

    def __del__(self):
        del self.hand
        del self.score
        del self
        return

