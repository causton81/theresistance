from tornado import web, websocket, ioloop
from sockjs.tornado import SockJSRouter, SockJSConnection
import json
import math
import random
import pdb


class Character(object):
    deck = {}

    def __init__(self, name, spy):
        self.name = name
        self.spy = spy
        self.group = []

        Character.deck[self.name] = self

    
    def get_name(self):
        return self.name


    def is_spy(self):
        return self.spy


    def sees(self, group, *args):
        self.group_seen = group
        self.group = args


    def knows_other_as(self, other):
        if other in self.group:
            return self.group_seen

        return "resistance"


class Rules(object):
    MIN_PLAYERS = 5
    FACTOR = 1.0/3.0

    RESISTANCE = Character("resistance", spy=False)
    MERLIN = Character("merlin", spy=False)
    PERCIVAL = Character("percival", spy=False)

    SPY = Character("spy", spy=True)
    ASSASSIN = Character("assassin", spy=True)
    MORDRED = Character("mordred", spy=True)
    OBERON = Character("oberon", spy=True)
    MORGANA = Character("morgana", spy=True)
    
    MERLIN.sees("spy", SPY, ASSASSIN, OBERON, MORGANA)
    PERCIVAL.sees("merlin", MERLIN, MORGANA)

    SPY.sees("spy", SPY, ASSASSIN, MORDRED)
    ASSASSIN.sees("spy", SPY, MORDRED, MORGANA)
    MORDRED.sees("spy", SPY, ASSASSIN, MORGANA)
    MORGANA.sees("spy", SPY, ASSASSIN, MORDRED)


    @staticmethod
    def num_spies_for_players(num_players):
        return int(math.ceil(Rules.FACTOR * num_players))


NOT_ENOUGH_PLAYERS = 'not.enough.players'

class MessageBundle(object):
    def __init__(self):
        self.code_formats = {}
        self.code_formats[NOT_ENOUGH_PLAYERS] = "Need at least {0} players to assign roles"

    def fill(self, code, *args):
        return self.code_formats[code]


bundle = MessageBundle()



class Game(object):

    def __init__(self, name):
        self.name = name
        self.players = []


    def add_player(self, p):
        if p in self.players:
            raise RuntimeError("Duplicate player added")

        self.players.append(p)


    def rem_player(self, p):
        self.players.remove(p)


    def num_players(self):
        return len(self.players)


    def get_players(self):
        return self.players


    def get_player_view(self, player):
        view = {}
        my_char = player.get_character()
        for p in self.get_players():
            other_char = p.get_character()
            view[p.get_name()] = my_char.knows_other_as(other_char)

        #view[player.get_name()] = my_char.get_name()

        return view


    def assign_roles(self, *enabled_characters):
        if self.num_players() < Rules.MIN_PLAYERS:
            raise RuntimeError(bundle.fill('not.enough.players', Rules.MIN_PLAYERS))

        print("Enabled: {}".format([c.name for c in enabled_characters]))

        spies = [c for c in enabled_characters if c.is_spy()]

        num_spies = Rules.num_spies_for_players(self.num_players())
        num_resist = self.num_players() - num_spies

        for i in range(len(spies), num_spies):
            spies.append(Rules.SPY)


        resist = [c for c in enabled_characters if not c.is_spy()]

        for i in range(len(resist), num_resist):
            resist.append(Rules.RESISTANCE)

        pool = spies[0:num_spies] + resist[0:num_resist]
        print("Pool: {}".format([c.name for c in pool]))

        for p in self.players:
            i = random.randrange(0, len(pool))
            c = pool[i]
            del pool[i]
            p.set_character(c)
            print("{0} assigned {1}".format(p.name, p.get_character().name))



class Player(object):
    def __init__(self, name):
        self.name = name
        self.character = Rules.RESISTANCE


    def get_name(self):
        return self.name


    def set_name(self, name):
        self.name = name


    def get_character(self):
        return self.character


    def set_character(self, character):
        self.character = character






class WSGame(object):
    EVT_CHANGE_NAME = 'change name'
    EVT_ADD_PLAYER = 'add player'
    EVT_REM_PLAYER = 'remove player'
    EVT_ASSIGN_ROLES = 'assign roles'
    EVT_ROLES_ASSIGNED = 'roles assigned'
    EVT_ERROR = 'error'

    FACTOR = (2 / 3)


    def __init__(self, name):
        self.name = name
        self.game = Game(name)
        self.connected_players = dict()
        self.characters = None
        self.unk = 0


    def update_player_views(self, evt, extra={}):
        if 0 == len(self.connected_players):
            return

        for ws,p in self.connected_players.items():
            data = {
                    "my_role": p.get_character().get_name(),
                    "players": self.game.get_player_view(p)
                    }

            data.update(extra)

            ws.send(json.dumps([evt, data]))


    def add_connection(self, ws):
        self.unk += 1
        p = Player("unknown{0}".format(self.unk))
        self.connected_players[ws] = p
        self.game.add_player(p)

        self.update_player_views(WSGame.EVT_ADD_PLAYER, {"player": p.get_name()})



    def connection_closed(self, ws):
        departing = self.connected_players.pop(ws)
        self.game.rem_player(departing)

        self.update_player_views(WSGame.EVT_REM_PLAYER, {"player": departing.get_name()})

    
    def process_event(self, ws, event, data):
        try:
            if WSGame.EVT_CHANGE_NAME  == event:
                p = self.connected_players[ws]
                p.set_name(data['player'])
                self.update_player_views(WSGame.EVT_ADD_PLAYER, {"player": p.get_name()})
            elif WSGame.EVT_ASSIGN_ROLES == event:
                specials = []
                if 'special_characters' in data:
                    for name in data['special_characters']:
                        if name in Character.deck:
                            specials.append(Character.deck[name])

                self.game.assign_roles(*specials)
                self.update_player_views(WSGame.EVT_ROLES_ASSIGNED)
            else:
                raise RuntimeError("Unrecognized event")

        except Exception as e:
            print(str(e))
            ws.send(json.dumps([WSGame.EVT_ERROR, {'message': str(e) }]))



games = {}


class WSGameHandler(SockJSConnection):
    def on_open(self, request):
        game_name = request.path.split('/')[2]

        if game_name not in games:
            print("Creating game '{}'".format(game_name))
            games[game_name] = WSGame(game_name)

        self.game = games[game_name]
        self.game.add_connection(self)


    def on_message(self, msg):
        event, data = json.loads(msg)
        self.game.process_event(self, event, data)


    def on_close(self):
        print("websocket closed")
        if hasattr(self, 'game'):
            self.game.connection_closed(self)
            self.game = None



def make_app():
    router = SockJSRouter(WSGameHandler, r'/game/(?:\w+)')
    app = web.Application(router.urls)
    return app



if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    ioloop.IOLoop.instance().start()
