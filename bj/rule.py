from collections import namedtuple
from fractions import Fraction

from bj.hand import Hand as H
from bj.game import GameStateDist

class BJRule(namedtuple('BJRule', 'name pay playHouse actions defaultDecks')):
	pass

def __BJ_pay(h, p):
	if p.isBust():
		return -1
	if p.isNat():
		return 0 if h.isNat() else Fraction(3,2)
	if h.isBust():
		return 1
	if h.isNat():
		return -1
	hm = h.value
	pm = p.value
	return 0 if hm == pm else 1 if pm > hm else -1

def __BJ_playHouse(gs):
	if gs.done:
		return GameStateDist.inject(gs)
	h = gs.currentHand()
	if h.canHit() and (h.value <= 16 or h.isA17()):
		return gs.hit()
	else:
		return GameStateDist.inject(gs.turnDone())

"""
Blackjack standard.

Blackjack pays 3:2. Dealer must hit soft-17.
"""
BJ = BJRule("Blackjack", __BJ_pay, __BJ_playHouse, ('H', 'S', 'D', 'P', 'U'), 8)

def __BJS_pay(h, p):
	if p.isBust():
		return -1
	if p.isNat():
		return 0 if h.isNat() else 1
	if h.isBust():
		return 0 if h.is22() else 1
	if h.isNat():
		return -1
	hm = h.value
	pm = p.value
	return 0 if hm == pm else 1 if pm > hm else -1

def __BJS_playHouse(gs):
	if gs.done:
		return GameStateDist.inject(gs)
	h = gs.currentHand()
	if h.canHit() and (h.value <= 16 or h.isA17()):
		return gs.hit()
	else:
		return GameStateDist.inject(gs.turnDone())

"""
Blackjack Switch (Las Vegas).

Cannot surrender. Blackjack pays 1:1. Dealer must hit soft-17 and pushes on 22.
We do not (yet) simulate or estimate a strategy for switching.
"""
BJS = BJRule("Blackjack Switch", __BJS_pay, __BJS_playHouse, ('H', 'S', 'D', 'P'), 8)

def __BJV_pay(h, p):
	if p.isBust():
		return -1
	if p.isNat():
		return 0 if h.isNat() else 1
	if h.isBust():
		return 1
	if h.isNat():
		return -1
	hm = h.value
	pm = p.value
	return 0 if hm == pm else 1 if pm > hm else -1

def __BJV_playHouse(gs):
	if gs.done:
		return GameStateDist.inject(gs)
	h = gs.currentHand()
	if h.canHit() and h.value <= 16:
		return gs.hit()
	else:
		return GameStateDist.inject(gs.turnDone())

"""
Blackjack, as seen on some of the video machines in Las Vegas.

Can only hit/switch. Blackjack pays 1:1.
"""
BJV = BJRule("Blackjack on the video machines", __BJV_pay, __BJV_playHouse, ('H', 'S'), 2)

assert BJS.pay(H(1,10,0,1), H(1,10,0,1)) == 0
assert BJS.pay(H(1,10,0,1), H(0,20)) == -1
assert BJS.pay(H(0,22), H(1,10,0,1)) == 1
assert BJS.pay(H(0,22), H(0,21)) == 0
assert BJS.pay(H(0,22), H(0,7)) == 0
assert BJS.pay(H(0,7), H(0,22)) == -1
assert BJS.pay(H(0,7), H(0,20)) == 1
assert BJS.pay(H(0,20), H(0,7)) == -1
