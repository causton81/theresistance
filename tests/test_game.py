import pytest
import math
import random


class Character(object):
    deck = {}

    def __init__(self, name, spy):
        self.name = name
        self.spy = spy
        self.group = []

        Character.deck[self.name] = self


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


    def num_spies_for_players(num_players):
        return math.ceil(Rules.FACTOR * num_players)


class GameX(object):

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
        for p in self.get_players():
            its_char = p.get_character()
            other_char = p.get_character()
            view[p.get_name()] = its_char.knows_other_as(other_char)

        return view


    def assign_roles(self, *enabled_characters):
        if self.num_players() < Rules.MIN_PLAYERS:
            raise RuntimeError("Need at least {0} players to assign roles".format(Rules.MIN_PLAYERS))

        spies = [c for c in enabled_characters if c.is_spy()]

        num_spies = Rules.num_spies_for_players(self.num_players())
        num_resist = self.num_players() - num_spies

        for i in range(len(spies), num_spies):
            spies.append(Rules.SPY)


        resist = [c for c in enabled_characters if not c.is_spy()]

        for i in range(len(resist), num_resist):
            resist.append(Rules.RESISTANCE)

        r = random.randrange(0, self.num_players())
        delta = rand_coprime(self.num_players())

        print("Using r={0} and delta={1}".format(r, delta))

        for i,c in enumerate(spies + resist):
            who = (r + i * delta) % self.num_players()
            self.players[who].set_character(c)

        for p in self.players:
            print("{0} assigned {1}".format(p.name, p.get_character().name))

def factor(val):
    rval = []

    if 2 == val: return rval
    if 0 == val % 2:
        rval.append(2)

    for i in range(3, val, 2):
        if 0 == val % i:
            rval.append(i)

    return rval


def rand_coprime(val):
    factors = factor(val)

    guess = random.randrange(1,val) % val
    for i in range(val):
        if 0 != guess and guess not in factors:
            return guess
        guess += 1

    return 1


class Player(object):
    def __init__(self, name):
        self.name = name
        self.character = None


    def get_name(self):
        return self.name


    def get_character(self):
        return self.character


    def set_character(self, character):
        self.character = character



def test_factor():
    assert [] == factor(2)
    assert [] == factor(3)
    assert [2] == factor(4)
    assert [] == factor(5)
    assert [2,3] == factor(6)
    assert [] == factor(7)
    assert [2] == factor(8)
    assert [3] == factor(9)
    assert [2,5] == factor(10)
    assert [3,5] == factor(15)
    assert [3,5,9,15] == factor(45)
    assert [3,11] == factor(33)


def test_character():
    assert "spy" == Rules.MERLIN.knows_other_as(Rules.SPY)
    assert "resistance" == Rules.MERLIN.knows_other_as(Rules.RESISTANCE)
    assert "resistance" == Rules.MERLIN.knows_other_as(Rules.MORDRED)

    assert "merlin" == Rules.PERCIVAL.knows_other_as(Rules.MERLIN)
    assert "merlin" == Rules.PERCIVAL.knows_other_as(Rules.MORGANA)
    assert "resistance" == Rules.PERCIVAL.knows_other_as(Rules.MORDRED)

    assert "resistance" == Rules.ASSASSIN.knows_other_as(Rules.MERLIN)
    assert "spy" == Rules.ASSASSIN.knows_other_as(Rules.SPY)



def test_game():
    g = GameX("unitgame")
    assert 0 == g.num_players()

    p0 = Player("p0")

    g.add_player(p0)
    assert 1 == g.num_players()

    with pytest.raises(RuntimeError):
        g.add_player(p0)
    assert 1 == g.num_players()

    g.rem_player(p0)
    assert 0 == g.num_players()

    with pytest.raises(RuntimeError):
        g.assign_roles([])


    for i in range(1, Rules.MIN_PLAYERS):
        p = Player("p{0}".format(i))
        g.add_player(p)

    with pytest.raises(RuntimeError):
        g.assign_roles([])


    g.add_player(p0)
    g.assign_roles()

    num_spies = 0
    num_resistance = 0
    num_merlin = 0

    for p in g.get_players():
        c = p.get_character()
        assert c
        assert c in Character.deck.values()

        if c.is_spy():
            num_spies += 1
        else:
            num_resistance += 1

        if Rules.MERLIN == c:
            num_merlin += 1

    assert 2 == num_spies
    assert 3 == num_resistance
    assert 0 == num_merlin



    g.assign_roles(Rules.MERLIN)

    num_spies = 0
    num_resistance = 0
    num_merlin = 0

    for p in g.get_players():
        c = p.get_character()
        assert c
        assert c in Character.deck.values()

        if c.is_spy():
            num_spies += 1
        else:
            num_resistance += 1

        if Rules.MERLIN == c:
            num_merlin += 1

    assert 2 == num_spies
    assert 3 == num_resistance
    assert 1 == num_merlin




    g.assign_roles(Rules.ASSASSIN, Rules.MORDRED, Rules.OBERON)

    num_spies = 0
    num_resistance = 0
    num_merlin = 0

    for p in g.get_players():
        c = p.get_character()
        assert c
        assert c in Character.deck.values()

        if c.is_spy():
            num_spies += 1
        else:
            num_resistance += 1

        if Rules.MERLIN == c:
            num_merlin += 1

    assert 2 == num_spies
    assert 3 == num_resistance
    assert 0 == num_merlin




    g.assign_roles(Rules.ASSASSIN, Rules.MERLIN)

    num_spies = 0
    num_resistance = 0
    num_merlin = 0

    for p in g.get_players():
        c = p.get_character()
        assert c
        assert c in Character.deck.values()

        if c.is_spy():
            num_spies += 1
        else:
            num_resistance += 1

        if Rules.MERLIN == c:
            num_merlin += 1

            view = g.get_player_view(p)
            assert 5 == len(view)
            for label in view.values():
                assert label == "resistance" or label == "spy"

    assert 2 == num_spies
    assert 3 == num_resistance
    assert 1 == num_merlin
