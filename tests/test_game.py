import pytest

from wsgame import *




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
    g = Game("unitgame")
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
