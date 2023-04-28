import pytest

from ddrmas_python.models.Agent import Agent
from ddrmas_python.models.LLiteral import LLiteral, Sign
from ddrmas_python.models.Literal import Literal
from ddrmas_python.models.Rule import Rule
from ddrmas_python.models.System import System



def create_alice():
    alice = Agent("alice")

    lit_ed = Literal(False, "ed", ["M"])
    print(repr(lit_ed))

    a_not_ed = LLiteral(alice, Literal(False, "ed", ["M"]))
    a_dc =  LLiteral(alice, Literal(True, "dc", ["M"]))
    r_a1 = Rule(a_not_ed, [a_dc])

    a_col = LLiteral(alice, Literal(True, "col", ["M"]))
    ed =  LLiteral(Sign.SCHEMATIC, Literal(True, "ed", ["M"]))
    r_a2 = Rule(a_col, [ed])

    a_not_col = a_col.negated()
    not_ed = ed.negated()
    r_a3 = Rule(a_not_col, [not_ed])

    alice.kb.union([r_a1, r_a2, r_a3])

    return alice


def create_bob():
    bob = Agent("bob")

    b_not_ed = LLiteral(bob, Literal(False, "ed", ["M"]))
    b_hv =  LLiteral(bob, Literal(True, "hv", ["M"]))
    r_b1 = Rule(b_not_ed, [b_hv])

    b_col = LLiteral(bob, Literal(True, "col", ["M"]))
    ed =  LLiteral(Sign.SCHEMATIC, Literal(True, "ed", ["M"]))
    r_b2 = Rule(b_col, [ed])

    b_not_col = b_col.negated()
    not_ed = ed.negated()
    r_b3 = Rule(b_not_col, [not_ed])

    bob.kb.union([r_b1, r_b2, r_b3])

    return bob


def create_charles():
    charles = Agent("charles")

    c_ed = LLiteral(charles, Literal(True, "ed", ["M"]))
    avl =  LLiteral(Sign.SCHEMATIC, Literal(True, "avl", ["M"]))
    r_c1 = Rule(c_ed, [avl])

    charles.kb.union([r_c1])

    return charles


def create_dennis():

    dennis = Agent("dennis")

    d_not_ed = LLiteral(dennis, Literal(False, "ed", ["M"]))
    am =  LLiteral(Sign.SCHEMATIC, Literal(True, "am", ["M"]))
    r_d1 = Rule(d_not_ed, [am])

    dennis.kb.union([r_d1])

    return dennis


def create_eric():

    eric = Agent("eric")

    e_not_ed = LLiteral(eric, Literal(True, "spa", ["M"]))
    e_hv =  LLiteral(eric, Literal(True, "hv", ["M"]))
    e_pbc =  LLiteral(eric, Literal(True, "pbc", ["M"]))
    r_e1 = Rule(e_not_ed, [e_hv, e_pbc])

    eric.kb.union([r_e1])

    return eric


def set_trusts(alice:Agent, bob:Agent, charles:Agent, dennis:Agent, eric:Agent):
    alice.trust[alice] = 1
    alice.trust[bob] = .4
    alice.trust[charles] = .6
    alice.trust[dennis] = .2
    alice.trust[eric] = .8

    bob.trust[alice] = .5
    bob.trust[bob] = 1
    bob.trust[charles] = .5
    bob.trust[dennis] = .5
    bob.trust[eric] = .5

    charles.trust[alice] = 1
    charles.trust[bob] = .4
    charles.trust[charles] = 1
    charles.trust[dennis] = .4
    charles.trust[eric] = 1

    dennis.trust[alice] = .4
    dennis.trust[bob] = .4
    dennis.trust[charles] = 1
    dennis.trust[dennis] = 1
    dennis.trust[eric] = 1

    eric.trust[alice] = .4
    eric.trust[bob] = .6
    eric.trust[charles] = .2
    eric.trust[dennis] = .8
    eric.trust[eric] = 1



def test_create_system():


    sis1 = System()
    
    alice = create_alice()
    bob = create_bob()
    charles = create_charles()
    dennis = create_dennis()
    eric = create_eric()

    sis1.agents += [alice, bob, charles, dennis, eric]

    set_trusts(alice, bob, charles, dennis, eric)

    

    