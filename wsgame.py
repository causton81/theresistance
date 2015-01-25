from tornado import web, websocket, ioloop
from sockjs.tornado import SockJSRouter, SockJSConnection
import json


class Game(object):
    EVT_JOIN = 'join game'
    EVT_ADD_PLAYER = 'add player'
    EVT_REM_PLAYER = 'remove player'


    def __init__(self, name):
        self.name = name
        self.players = dict()


    def add_player(self, ws, name):
        self.players[ws] = name

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
        rv = list(self.players.values())
        rv.sort()
        return rv




games = {}


class GameHandler(SockJSConnection):
    def on_open(self, request):
        pass


    def on_message(self, msg):
        event, data = json.loads(msg)

        if Game.EVT_JOIN  == event:
            game_name = data['game']
            player = data['player']

            if game_name not in games:
                games[game_name] = Game(game_name)

            self.game = games[game_name]

            self.game.add_player(self, player)



    def on_close(self):
        print("websocket closed")
        if hasattr(self, 'game'):
            self.game.remove_player(self)
            self.game = None



def make_app():
    router = SockJSRouter(GameHandler, '/game')
    app = web.Application(router.urls)
    return app



if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    ioloop.IOLoop.instance().start()
