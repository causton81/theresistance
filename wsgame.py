from tornado import web, websocket, ioloop
from sockjs.tornado import SockJSRouter, SockJSConnection
import json
import math


class Game(object):
    EVT_JOIN = 'join game'
    EVT_ADD_PLAYER = 'add player'
    EVT_REM_PLAYER = 'remove player'
    EVT_ASSIGN_ROLES = 'assign roles'
    EVT_ERROR = 'error'
    MSG_NEED_MORE_PLAYERS = 'at least five players must join to assign roles'

    FACTOR = (2 / 3)


    def __init__(self, name):
        self.name = name
        self.players = dict()
        self.characters = None


    def add_player(self, ws, name):
        self.players[ws] = name

        print("New player '{}'".format(name))

        self.broadcast(Game.EVT_ADD_PLAYER, {
            "player": name,
            "players":  self.get_players_info()
            })



    def remove_player(self, ws):
        departing = self.players.pop(ws)

        self.broadcast(Game.EVT_REM_PLAYER, {
            "player": departing,
            "players":  self.get_players_info()
            })


    def broadcast(self, evt, data):
        if 0 == len(self.players):
            return

        for ws,name in self.players.items():
            ws.broadcast(self.players.keys(), json.dumps([evt, data]))
            #this was the easiest way I could find to get a random item...
            break

    
    def get_players_info(self):
        rv = {}
        for i,p in enumerate(self.players.values()):
            rv[p] = self.characters[i] if self.characters else "resistance"

        return rv

    
    def num_players(self):
        return len(self.players)

    
    def process_event(self, ws, event, data):
        if Game.EVT_JOIN  == event:
            player = data['player']

            self.add_player(ws, player)

        elif Game.EVT_ASSIGN_ROLES == event:
            if self.num_players() < 5:
                ws.send(json.dumps([Game.EVT_ERROR, {'message': Game.MSG_NEED_MORE_PLAYERS }]))
                return

            num_resistance = math.floor(Game.FACTOR * self.num_players())
            num_spies = self.num_players() - num_resistance

            self.characters = []
            for i in range(num_resistance):
                self.characters.append('resistance')

            for i in range(num_spies):
                self.characters.append('spy')

            self.broadcast(Game.EVT_ASSIGN_ROLES, {
                "players":  self.get_players_info()
                })



games = {}


class GameHandler(SockJSConnection):
    def on_open(self, request):
        game_name = request.path.split('/')[2]

        if game_name not in games:
            print("Creating game '{}'".format(game_name))
            games[game_name] = Game(game_name)

        self.game = games[game_name]


    def on_message(self, msg):
        event, data = json.loads(msg)

        self.game.process_event(self, event, data)



    def on_close(self):
        print("websocket closed")
        if hasattr(self, 'game'):
            self.game.remove_player(self)
            self.game = None



def make_app():
    router = SockJSRouter(GameHandler, r'/game/(?:\w+)')
    app = web.Application(router.urls)
    return app



if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    ioloop.IOLoop.instance().start()
