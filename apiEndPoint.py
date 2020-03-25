from flask import Flask, request
from FiveCrowns import Game

api = Flask(__name__)

@api.route('/deck', methods=['GET'])
def get_deck():
    g = Game()
    return g.getDeck()

@api.route('/card', methods=['GET'])
def get_random_card():
    g = Game()
    return g.randomCardFromDeck()


if __name__ == '__main__':
    api.run(debug=True, port=5000)
