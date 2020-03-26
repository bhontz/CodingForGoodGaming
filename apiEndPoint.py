"""
    execute this module to start webserver.
    Access http://localhost:5000/<route>.
    e.g.: http://localhost:5000/deck
"""
from flask import Flask, request
from FiveCrowns import Game

api = Flask(__name__)
thisGame = Game()

@api.route('/deck', methods=['GET'])
def getDeck():
    return thisGame.getDeck()

@api.route('/addPlayer', methods=['GET'])
def addPlayer():
    return thisGame.addPlayer("Blazed Thorny")

@api.route('/dealToPlayers', methods=['GET'])
def dealPlayers():
    return thisGame.dealToPlayers()

# this will be the first PUT call
# @api.route('/showHand', methods=['GET'])
# def showPlayerHand():
#     return thisGame.showPlayerHand()

@api.route('/showDiscard', methods=['GET'])
def showDiscard():
    return thisGame.showDiscard()

# @api.route('/shuffledeck', methods=['GET'])
# def shuffleDeck():
#     return thisGame.shuffleDeck()

@api.route('/randomCard', methods=['GET'])
def get_random_card():
    return thisGame.randomCardFromDeck()

if __name__ == '__main__':
    api.run(debug=True, port=5000)
