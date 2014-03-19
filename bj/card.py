from collections import namedtuple
from fractions import Fraction
from bj.prob import ProbDist

class CardState(object):
	"""State of the cards, either real or modelled. Immutable."""
	def draw(self, v=None):
		"""
		@return: ProbDist([((i, state), prob)])
		"""
		raise NotImplementedError

	@classmethod
	def fromState(cls, total):
		raise NotImplementedError

class NullCardState(CardState, namedtuple('NullCardState', '')):
	"""Doesn't count any cards."""
	def draw(self, v=None):
		if v is None:
			return ProbDist([((i, self), Fraction(1 if i != 0 else 4, 13)) for i in xrange(10)])
		else:
			return ProbDist([((v, self), Fraction(1))])

	@classmethod
	def fromState(cls, total):
		return cls()

	def __str__(self):
		return '(-)'

class TotalCardState(CardState, namedtuple('TotalCardState', 'decks total state')):
	"""The actual state of the cards, or alternatively a perfect counter's view."""
	def __new__(cls, decks=6, state=None):
		self = super(TotalCardState, cls).__new__(cls, decks, tuple([16*decks] + ([4*decks]*9)), tuple(state or [0]*10))
		if any(self.state[i] > self.total[i] for i in xrange(10)):
			raise ValueError
		return self

	def __mknext(self, i, prob):
		newstate = list(self.state)
		newstate[i] += 1
		return (i, self.__class__(self.decks, newstate))

	def draw(self, v=None):
		cardsleft = self.decks * 52 - sum(self.state)
		dist = []
		if v is None:
			for i in xrange(10):
				prob = Fraction(self.total[i] - self.state[i], cardsleft)
				if not prob: continue
				dist.append((self.__mknext(i, prob), prob))
		else:
			prob = Fraction(self.total[v] - self.state[v], cardsleft)
			if not prob: raise ValueError()
			dist.append((self.__mknext(v, prob), Fraction(1)))
		return ProbDist(dist)

	def __str__(self):
		return repr(self.state)

class PartialAJHLCardState(CardState, namedtuple('PartialAJHLCardState', 'decks total state')):
	"""Counts tens (10JQK), aces, lo (2345), hi (6789) separately."""
	def __new__(cls, decks=6, state=None):
		if type(decks) != int: raise ValueError
		self = super(PartialAJHLCardState, cls).__new__(cls, decks, tuple(4*decks*x for x in [4,1,4,4]), tuple(state or [0]*4))
		if any(self.state[i] > self.total[i] for i in xrange(4)):
			raise ValueError
		return self

	def __mknext(self, i, v, prob):
		newstate = list(self.state)
		newstate[i] += 1
		return (v, self.__class__(self.decks, newstate))

	def draw(self, v=None):
		cardsleft = self.decks * 52 - sum(self.state)
		dist = []
		if v is None:
			for i in xrange(4):
				prob = Fraction(self.total[i] - self.state[i], cardsleft)
				if not prob: continue
				if i == 0 or i == 1:
					dist.append((self.__mknext(i, i, prob), prob))
				elif i == 2: # 2,3,4,5
					for j in xrange(4):
						dist.append((self.__mknext(i, 2+j, prob/4), prob/4))
				elif i == 3: # 6,7,8,9
					for j in xrange(4):
						dist.append((self.__mknext(i, 6+j, prob/4), prob/4))
		else:
			if v == 0 or v == 1:
				i = v
			elif 2 <= v <= 5:
				i = 2
			elif 6 <= v <= 9:
				i = 3
			prob = Fraction(self.total[i] - self.state[i], cardsleft)
			if not prob: raise ValueError()
			dist.append((self.__mknext(i, v, prob), Fraction(1)))
		return ProbDist(dist)

	def __str__(self):
		return repr(self.state)

c = TotalCardState()
assert c.total == (96, 24, 24, 24, 24, 24, 24, 24, 24, 24)
assert c.state == (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
n = c.draw()
assert n.dist[0][0][1].state == (1, 0, 0, 0, 0, 0, 0, 0, 0, 0)
assert n.dist[1][0][1].state == (0, 1, 0, 0, 0, 0, 0, 0, 0, 0)
