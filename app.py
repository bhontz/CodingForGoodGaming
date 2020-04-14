"""
    execute this module to start webserver.
    Access http://localhost:5000/<route>.
    e.g.: http://localhost:5000/deck
"""
import json
from flask import Flask, request
from FiveCrownsGame import Game

app = Flask(__name__)
# app.config["thisGame"] = Game()
thisGame = Game()

# need to edit replace: app.config.get("thisGame") with thisGame

"""
    API methods for client GAME INITIALIZATION:
    startGame: interface for inviting players has the following UI components:
    - entry of list of email addresses of the players to invite for this game (they receive an email with a URL)
    - setting to start the game after 'n' of the players have checked in.
    - ability to pause the game between rounds  
    test POST: {"invite": ["bhontz@gmail.com", "brad.hontz@pinpointview.com"], "startGameAfter": 1}

    pauseGame: break point in the game after the current round completes
        Server returns: confirmation of game pause after round n [GET]

    resumeGame: resume game paused by pauseGame [GET]
        Server returns: confirmation of game resumed    
"""

@app.route("/createGame", methods=['POST'])
def createGame():
    status = "nothing happened"

    param = request.form["data"]
    # param = request.form.get("data")
    if param:
        obj = json.loads(param)
        if obj['invite']:
            status = thisGame.createGame(obj['invite'], obj['startGameAfter'])

    return status


"""
    API methods for client PLAYER:
    playerReady: executing the URL emailed from the Game, indication that player is ready to play [POST playerID, playername]
        server returns: Player.hand, Game.discard, and potentially "your turn".

    myTurn: client PUT [POST playerID] every 10 seconds
        server returns: Player.score, Game.round, Game.discard, if player's turn, then message "your turn" or "player [name] is out, your last turn"

    Player Turn API methods:
        pickDeck: player selects the top card from the deck
            server returns: Player.hand

        pickDiscard: player selects the top card from the discard [mutually exclusive with pickDeck]
            server returns: Player.hand, Game.discard (updated)

        discard: player selects discard from their hand [POST card]
            server returns: Game.discard

        out: player indicates that they are going out during this round [POST playerId]

        pass: player indicates that they're done and control passes to next player [mutually exclusive with out] [POST playerID]
"""


@app.route('/playerReady', methods=['GET'])
def playerCheckIn():
    id = request.args.get('id', default=-1, type=int)
    name = request.args.get('name', default="undefined", type=str)

    s = "playerReady error"

    if id != -1:
        s = thisGame.playerCheckIn(id, name)

    return s


@app.route('/playerStatus', methods=['GET'])
def playerStatus():
    id = request.args.get('id', default=-1, type=int)

    s = "playerStatus error"
    if id != -1:
        s = thisGame.playerGameStatus(id)

    return s


@app.route('/pickDeck', methods=['GET'])
def pickDeck():
    id = request.args.get('id', default=-1, type=int)

    s = "pickDeck error"
    if id != -1:
        s = thisGame.pickFromDeck(id)

    return s


@app.route('/pickDiscard', methods=['GET'])
def pickDiscard():
    id = request.args.get('id', default=-1, type=int)

    s = "pickDiscard error"
    if id != -1:
        s = thisGame.pickFromDiscard(id)

    return s


@app.route('/discard', methods=['GET'])
def discard():
    id = request.args.get('id', default=-1, type=int)
    cardJSON = request.args.get('card', default="{}", type=str)

    s = "discard error"
    if id != -1 and cardJSON != "{}":
        s = thisGame.playerDiscard(id, cardJSON)

    return s


@app.route('/pass', methods=['GET'])
def playerPass():
    id = request.args.get('id', default=-1, type=int)

    s = "pass error"
    if id != -1:
        s = thisGame.playerPass(id)

    return s


@app.route('/out', methods=['GET'])
def playerOut():
    id = request.args.get('id', default=-1, type=int)
    outhand = request.args.get('outhand', default="{}", type=str)

    s = "out error"
    if id != -1:
        s = thisGame.playerOut(id, outhand)

    return s


@app.route('/nextround', methods=['GET'])
def nextRound():
    id = request.args.get('id', default=-1, type=int)

    s = "nextround error"
    if id != -1:
        s = thisGame.startNextRound(id)

    return s


@app.route('/endGame', methods=['GET'])
def endGame():
    return thisGame.endGame()


@app.route('/peakIds', methods=['GET'])
def peakIds():
    return thisGame.peakIds()

if __name__ == '__main__':
    # app.config["thisGame"] = Game()
    app.run(debug=True, port=8080)
    #app.run(debug=True, host='192.168.100.35', port=5000)
