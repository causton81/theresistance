from wsgame import *

class MockSocket(object):
    def broadcast(self, sock_list, msg):
        pass


def test_game():
    g = Game("unitgame")

    ws1 = MockSocket()

    g.add_player(ws1, "player1")

