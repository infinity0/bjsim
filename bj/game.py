from collections import namedtuple
from bj.prob import ProbDist
from bj.hand import Hand as H


class GameState(namedtuple('GameState', 'cards hands turn done')):
	"""State of the game. Immutable.

	Attributes:
		cards: A CardState
		hands: List of hands for each player. Dealer is 0 and play proceeds
			from the highest index downwards.
		turn:
			Index into self.hands for the current player whose turn it is.
		done:
			Whether the current player's turn is done.
	"""
	def __new__(cls, cards, hands, turn=None, done=False):
		if not hands or len(hands) < 2: raise ValueError
		if turn is None: turn = len(hands) - 1
		if not 0 <= turn < len(hands): raise ValueError
		return super(GameState, cls).__new__(cls, cards, tuple(hands), turn, done)

	def isDealComplete(self):
		"""Has everyone been dealt 2 cards."""
		return all(h.isDealComplete() for h in self.hands)

	def turnDone(self):
		"""Finish the current player's turn."""
		return self.__class__(self.cards, self.hands, self.turn, True)

	def nextTurn(self):
		"""Move to the next player's turn."""
		if not self.done: raise ValueError()
		return self.__class__(self.cards, self.hands, self.turn-1 if self.turn else None)

	def turnDoneNext(self):
		"""Finish """
		return self.turnDone().nextTurn()

	def newGame(self):
		"""Start a new game, i.e. reset hands but keep the card state."""
		if self.turn != len(self.hands) - 1 or self.done: raise ValueError()
		return self.__class__(self.cards, [H()] * len(self.hands))

	def __str__(self):
		return "%s %s : P%s %s" % (",".join("%4s" % str(h) for h in self.hands), self.cards, self.turn, 'played' if self.done else 'to play')

	def currentHand(self):
		"""Get the hand of the current player."""
		return self.hands[self.turn]

	def __mkHand(self, i, h=None):
		hh = self.hands
		return hh if h is None else hh[:i] + (h,) + hh[i+1:]

	def hit(self, v=None):
		h = self.currentHand()
		if not h.canHit():
			return GameStateDist.inject(self.turnDone())
		cdist = self.cards.draw(v)
		dist = []
		for ((card, nextcards), prob) in cdist.dist:
			dist.append((self.__class__(nextcards, self.__mkHand(self.turn, h.add(card)), self.turn), prob))
		return GameStateDist(dist)

	def replaceHand(self, i, h=None):
		# should only really be used for display purposes
		return self.__class__(self.cards, self.__mkHand(i, h), self.turn, self.done)

	def filterCardState(self, cls):
		"""Change the class of the CardState."""
		return self.__class__(cls.fromState(self), self.hands, self.turn, self.done)

	def describeHands(self):
		"""Describe how well each player did against the house.

		Each player's hand is replaced by a two-character string:

		xx lost (bust) vs the house
		++ won vs a bust house
		<< lost vs the house
		== tied with the house (inc. bust vs bust, nat vs nat)
		>> won vs the house
		AJ won (blackjack) vs the house
		"""
		h0 = self.hands[0] # house cards
		if h0.isBust():
			s = lambda h: "==" if h.isBust() else "++"
		elif h0.isNat():
			s = lambda h: "xx" if h.isBust() else "==" if h.isNat() else "<<"
		else:
			v = h0.value
			s = lambda h: "xx" if h.isBust() else "AJ" if h.isNat() else "<<" if h.value < v else ">>" if h.value > v else "=="
		return self.__class__(self.cards, [str(h0)] + map(s, self.hands[1:]), self.turn, self.done)


class GameStateDist(ProbDist):

	@classmethod
	def initGame(cls, numHands, initCards):
		return cls.inject(GameState(initCards, [None]*numHands))

	def expectPay(self, f):
		return [0] + [self.expect(lambda gs: f(gs.hands[0], gs.hands[i])) for i in xrange(1, self.numPlayers())]

	def allDone(self):
		return all(gs.done for gs, p in self.dist)

	def allDealComplete(self):
		return all(gs.isDealComplete() for gs, p in self.dist)

	def allOnTurn(self, i):
		return all(gs.turn == i for gs, p in self.dist)

	def numPlayers(self):
		n = len(self.dist[0][0].hands)
		assert all(len(gs.hands) == n for gs, p in self.dist)
		return n

	def _playUntilDone(self, f):
		"""Keep applying f until the turn is done."""
		gsd = self
		if not gsd.allDealComplete():
			raise ValueError
		while not gsd.allDone():
			gsd = gsd.bind(f)
		return gsd

	def execRound(self, strats, r=None):
		gsd = self
		if r is None:
			r = self.numPlayers() - 1
		if not gsd.allOnTurn(r):
			raise ValueError
		for i in xrange(r, -1, -1):
			gsd = gsd._playUntilDone(strats[i])
			assert gsd.allOnTurn(i) and gsd.allDone()
			# safe to copy gs.hands by reference because old wrapper is never used
			gsd = gsd.map(GameState.nextTurn)
		return gsd

	def dealNewRound(self, cards=None):
		gsd = self
		gsd = gsd.map(GameState.newGame)
		hit = lambda gs: gs.hit(cards.pop(0) if cards else None)
		for i in xrange(2 * self.numPlayers()):
			gsd = gsd.bind(hit).map(GameState.turnDoneNext)
		assert gsd.allDealComplete()
		return gsd


from bj.card import TotalCardState
from bj.rule import BJS
assert GameStateDist.inject(GameState(TotalCardState(), [H(1,10,0,1),H(0,20,0,0)], 0))._playUntilDone(BJS.playHouse).expectPay(BJS.pay)[1] == -1.0
assert GameStateDist.inject(GameState(TotalCardState(), [H(1,10,0,1),H(1,10,0,1)], 0))._playUntilDone(BJS.playHouse).expectPay(BJS.pay)[1] == 0.0
