from wsgame import *
import pytest
import urllib.parse
import json
from tornado import web, websocket, testing



class Helper(object):
    def __init__(self, test):
        self.test = test
        http = urllib.parse.urlparse(self.test.get_url(''))
        self.url = 'ws://{}/game/causton/websocket'.format(http.netloc)


    def connect(self):
        ws = yield websocket.websocket_connect(url=self.url, io_loop=self.test.io_loop)
        return ws

    
    def send(self, ws, event, data):
        ws.write_message(json.dumps([event, data]))


    def recv(self, ws):
        res = yield ws.read_message()
        return json.loads(res)



class TestWSGame(testing.AsyncHTTPTestCase):
    def get_app(self):
        return make_app()


    @testing.gen_test
    def test_no_special_characters(self):
        h = Helper(self)

        ws1 = yield from h.connect()
        event, data = yield from h.recv(ws1)
        assert WSGame.EVT_ADD_PLAYER == event
        assert data == {"player": "unknown1", "players": {"unknown1": "resistance"} }

        h.send(ws1, WSGame.EVT_CHANGE_NAME, {"player": "causton"})

        event, data = yield from h.recv(ws1)
        assert WSGame.EVT_ADD_PLAYER == event
        assert data == {"player": "causton", "players": {"causton": "resistance"} }


        ws2 = yield from h.connect()
        h.send(ws2, WSGame.EVT_CHANGE_NAME, {"player": "kaladin"})

        event, data = yield from h.recv(ws2)
        assert WSGame.EVT_ADD_PLAYER == event
        assert data == {"player": "unknown2", "players": {"causton": "resistance", "unknown2": "resistance"} }
        event, data = yield from h.recv(ws2)
        assert WSGame.EVT_ADD_PLAYER == event
        assert data == {"player": "kaladin", "players": {"causton": "resistance", "kaladin": "resistance"} }

        event, data = yield from h.recv(ws1)
        assert WSGame.EVT_ADD_PLAYER == event
        assert data == {"player": "unknown2", "players": {"causton": "resistance", "unknown2": "resistance"} }
        event, data = yield from h.recv(ws1)
        assert WSGame.EVT_ADD_PLAYER == event
        assert data == {"player": "kaladin", "players": {"causton": "resistance", "kaladin": "resistance"} }


        h.send(ws1, WSGame.EVT_ASSIGN_ROLES, {})

        event, data = yield from h.recv(ws1)
        assert WSGame.EVT_ERROR == event
        assert {'message': bundle.fill(NOT_ENOUGH_PLAYERS) } == data

        socks = [ws1, ws2]
        players = {"causton": "resistance", "kaladin": "resistance"}
        for i in range(3,6):
            name = "player{}".format(i)
            unk = "unknown{}".format(i)
            ws = yield from h.connect()
            socks.append(ws)

            h.send(ws, WSGame.EVT_CHANGE_NAME, {"player": name})
            players[unk] = 'resistance'

            results = yield [s.read_message() for s in socks]
            for res in results:
                event, data = json.loads(res)
                assert WSGame.EVT_ADD_PLAYER == event
                assert data == {"player": unk, "players": players }

            players.pop(unk)
            players[name] = 'resistance'

            results = yield [s.read_message() for s in socks]
            for res in results:
                event, data = json.loads(res)
                assert WSGame.EVT_ADD_PLAYER == event
                assert data == {"player": name, "players": players }




        msg = [WSGame.EVT_ASSIGN_ROLES, {}]
        ws1.write_message(json.dumps(msg))
        results = yield [s.read_message() for s in socks]

        for res in results:
            event,data = json.loads(res)
            assert WSGame.EVT_ASSIGN_ROLES == event




        ws1.close()
        res = yield ws2.read_message()
        del players['causton']
        event, data = json.loads(res)
        assert WSGame.EVT_REM_PLAYER == event
        #assert data == {"player": "causton", "players": players }
        assert data["player"] == "causton"
        assert "causton" not in data["players"]
        assert "player3" in data["players"]
