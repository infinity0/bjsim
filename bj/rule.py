from collections import namedtuple
from bj.hand import H
from bj.game import GameStateDist

class BJRule(namedtuple('BJRule', 'pay playHouse actions defaultDecks')):
	"""Rules of the game.

	We always assume a "no hole card" game, i.e. dealer does not play 2nd card
	until player has finished.

	Attributes:
		pay: function that determines payout based on final GameState
		playHouse: function that determines how the house plays
		actions: A tuple containing the possible player actions:
			H: hit
			S: stick
			D: double: double bet, hit once, then stick.
			P: split: double bet, then play 2 games each starting from one card.
				Currently we assume that any action after this is allowed,
				including doubling (allowed in most real casinos) and hitting
				aces (not allowed in most real casinos).
			U: surrender: immediately forfeit but only lose half your bet
		defaultDecks: default number of decks
	"""

def __playHouse_h17(gs):
	"""House hits on soft-17."""
	if gs.done:
		return GameStateDist.inject(gs)
	h = gs.hand()
	if h.canHit() and (h.v() <= 16 or h.isA17()):
		return gs.hit()
	else:
		return GameStateDist.inject(gs.turnDone())

def __playHouse_s17(gs):
	"""House sticks on soft-17."""
	if gs.done:
		return GameStateDist.inject(gs)
	h = gs.hand()
	if h.canHit() and h.v() <= 16:
		return gs.hit()
	else:
		return GameStateDist.inject(gs.turnDone())

def __BJ_pay(h, p):
	if p.isBust():
		return -1
	if p.isNat():
		return 0 if h.isNat() else 1.5
	if h.isBust():
		return 1
	if h.isNat():
		return -1
	hm = h.v()
	pm = p.v()
	return 0 if hm == pm else 1 if pm > hm else -1

"""
Blackjack (Las Vegas).

Can surrender. Blackjack pays 3:2. Dealer hits soft-17.
"""
BJ = BJRule(__BJ_pay, __playHouse_h17, ('H', 'S', 'D', 'U', 'P'), 8)

def __BJS_pay(h, p):
	if p.isBust():
		return -1
	if p.isNat():
		return 0 if h.isNat() else 1
	if h.isBust():
		return 0 if h.is22() else 1
	if h.isNat():
		return -1
	hm = h.v()
	pm = p.v()
	return 0 if hm == pm else 1 if pm > hm else -1

"""
Blackjack Switch (Las Vegas).

Cannot surrender. Blackjack pays 1:1. Dealer hits soft-17 and pushes on 22.
We do not (yet) simulate or estimate a strategy for switching.
"""
BJS = BJRule(__BJS_pay, __playHouse_h17, ('H', 'S', 'D', 'P'), 8)

def __BJV_pay(h, p):
	if p.isBust():
		return -1
	if p.isNat():
		return 0 if h.isNat() else 1
	if h.isBust():
		return 1
	if h.isNat():
		return -1
	hm = h.v()
	pm = p.v()
	return 0 if hm == pm else 1 if pm > hm else -1

"""
Blackjack, as seen on some of the video machines in Las Vegas.

Can only hit/switch. Blackjack pays 1:1. Dealer sticks soft-17.
"""
BJV = BJRule(__BJV_pay, __playHouse_s17, ('H', 'S'), 2)

assert BJS.pay(H(1,10,0,1), H(1,10,0,1)) == 0
assert BJS.pay(H(1,10,0,1), H(0,20)) == -1
assert BJS.pay(H(0,22), H(1,10,0,1)) == 1
assert BJS.pay(H(0,22), H(0,21)) == 0
assert BJS.pay(H(0,22), H(0,7)) == 0
assert BJS.pay(H(0,7), H(0,22)) == -1
assert BJS.pay(H(0,7), H(0,20)) == 1
assert BJS.pay(H(0,20), H(0,7)) == -1
