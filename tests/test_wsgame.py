import py.test
import urllib.parse
import json
from tornado import web, websocket, testing
from os import path
import sys

top_dir = path.abspath(path.join(path.dirname(__file__), '..'))
sys.path.append(top_dir)
from wsgame import Game, make_app


class TestGame(testing.AsyncHTTPTestCase):
    def get_app(self):
        return make_app()


    @testing.gen_test
    def test_no_special_characters(self):
        http = urllib.parse.urlparse(self.get_url(''))
        url = 'ws://{}/game/websocket'.format(http.netloc)

        ws1 = yield websocket.websocket_connect(url=url, io_loop=self.io_loop)

        msg = [Game.EVT_JOIN, {"game": "causton", "player": "causton"}]
        ws1.write_message(json.dumps(msg))

        res = yield ws1.read_message()
        event, data = json.loads(res)
        assert Game.EVT_ADD_PLAYER == event
        assert data == {"player": "causton", "players": ["causton"]}


        ws2 = yield websocket.websocket_connect(url=url, io_loop=self.io_loop)
        msg = [Game.EVT_JOIN, {"game": "causton", "player": "kaladin"}]
        ws2.write_message(json.dumps(msg))

        res = yield ws2.read_message()
        event, data = json.loads(res)
        assert Game.EVT_ADD_PLAYER == event
        assert data == {"player": "kaladin", "players": ["causton", "kaladin"]}

        res = yield ws1.read_message()
        event, data = json.loads(res)
        assert Game.EVT_ADD_PLAYER == event
        assert data == {"player": "kaladin", "players": ["causton", "kaladin"]}



        ws1.close()
        res = yield ws2.read_message()
        event, data = json.loads(res)
        assert Game.EVT_REM_PLAYER == event
        assert data == {"player": "causton", "players": ["kaladin"]}
