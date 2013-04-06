from collections import namedtuple
from bj.prob import ProbDist

class GameState(namedtuple('GameState', 'cards hands turn done')):
	"""State of the game. Immutable."""
	def __new__(cls, cards, hands, turn=None, done=False):
		if not hands or len(hands) < 2: raise ValueError
		if turn is None: turn = len(hands) - 1
		if not 0 <= turn < len(hands): raise ValueError
		self = super(GameState, cls).__new__(cls, cards, tuple(hands), turn, done)
		return self

	def isDealComplete(self):
		return all(h.isDealComplete() for h in self.hands)

	def turnDone(self):
		"""Note: DO NOT use self after this operation."""
		return self.__class__(self.cards, self.hands, self.turn, True)

	def nextTurn(self):
		"""Note: DO NOT use self after this operation."""
		if not self.done: raise ValueError()
		return self.__class__(self.cards, self.hands, self.turn-1 if self.turn else None)

	def resetHands(self):
		if self.turn != len(self.hands) - 1 or self.done: raise ValueError()
		return self.__class__(self.cards, [H()] * len(self.hands))

	def __str__(self):
		return "%s %s : P%s %s" % (",".join("%4s" % str(h) for h in self.hands), self.cards, self.turn, 'played' if self.done else 'to play')

	def hand(self):
		return self.hands[self.turn]

	def simplifyCards(self, cls):
		return self.__class__(cls.fromState(self), self.hands, self.turn, self.done)

	def simplifyHands(self):
		h0 = self.hands[0] # house cards
		if h0.isBust() or h0.isNat():
			def s(h): return H(0,23) if h.isBust() else h if h.isNat() else H(0,21)
		else:
			v = h0.v()
			def s(h): return H(0,23) if h.isBust() else h if h.isNat() else H(0, v-1 if h.v() < v else v+1 if h.v() > v else v)
		return self.__class__(self.cards, map(s, self.hands), self.turn, self.done)

	def __mkHand(self, i, h=None):
		if h is None: return self.hands
		hh = list(self.hands)
		hh[i] = h
		return tuple(hh)

	def replaceHand(self, i, h=None):
		# should only really be used for display purposes
		return self.__class__(self.cards, self.__mkHand(i, h), self.turn, self.done)

	def hit(self, v=None):
		h = self.hand()
		if not h.canHit():
			return GameStateDist.inject(self.turnDone())
		cdist = self.cards.draw(v)
		dist = []
		for ((card, nextcards), prob) in cdist.dist:
			dist.append((self.__class__(nextcards, self.__mkHand(self.turn, h.add(card)), self.turn), prob))
		return GameStateDist(dist)

class GameStateDist(ProbDist):

	@classmethod
	def initGame(cls, numHands, initCards):
		return cls.inject(GameState(initCards, [None]*numHands))

	def expectPay(self, f, l=None):
		if l is None:
			l = len(self.dist[0][0].hands)
		return [0] + [self.expect(lambda gs: f(gs.hands[0], gs.hands[i])) for i in xrange(1,l)]

	def playLoopUntilDone(self, f):
		"""Keep applying f until the turn is done."""
		gsd = self
		if any(not gs.isDealComplete() for gs, p in gsd.dist):
			raise ValueError
		while any(not gs.done for gs, p in gsd.dist):
			gsd = gsd.bind(f)
		return gsd

	def execRound(self, strats, r=None):
		gsd = self
		if r is None:
			r = len(gsd.dist[0][0].hands) - 1
		if any(gs.turn != r for gs, p in gsd.dist):
			raise ValueError
		for i in xrange(r, -1, -1):
			gsd = gsd.playLoopUntilDone(strats[i])
			assert all(gs.turn == i and gs.done for gs, p in gsd.dist)
			# safe to copy gs.hands by reference because old wrapper is never used
			gsd = gsd.map(lambda gs: gs.nextTurn())
		return gsd

	def dealNewRound(self, n=None, cards=None):
		gsd = self
		if n is None:
			n = len(gsd.dist[0][0].hands)
		gsd = gsd.map(GameState.resetHands)
		hit = lambda gs: gs.hit(cards.pop(0) if cards else None)
		for i in xrange(2 * n):
			gsd = gsd.bind(hit).map(lambda gs: gs.turnDone().nextTurn())
		assert all(gs.isDealComplete() for gs, p in gsd.dist)
		return gsd

from bj.hand import H
from bj.card import TotalCardState
from bj.rule import BJS
assert GameStateDist.inject(GameState(TotalCardState(), [H(1,10,0,1),H(0,20,0,0)], 0)).playLoopUntilDone(BJS.playHouse).expectPay(BJS.pay)[1] == -1.0
assert GameStateDist.inject(GameState(TotalCardState(), [H(1,10,0,1),H(1,10,0,1)], 0)).playLoopUntilDone(BJS.playHouse).expectPay(BJS.pay)[1] == 0.0
