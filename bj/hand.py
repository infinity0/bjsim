from collections import namedtuple

def genvalues(aces, osum):
	return tuple(x+osum for x in ([1, 11] if aces else [0]))

class H(namedtuple('H', 'aces osum fst snd')):
	"""A hand of cards."""
	def __new__(cls, aces=0, osum=0, fst=None, snd=None):
		self = super(H, cls).__new__(cls, aces, osum, fst, snd)
		self.values = genvalues(self.aces, self.osum)
		return self

	def isNat(self):
		# TODO: return false after switching
		return self.aces == 1 and self.osum == 10 and self.cardsDealt() == 2

	def isA17(self):
		return self.aces == 1 and self.osum == 6

	def is22(self):
		# 22s are treated specially in Blackjack Switch, so account for them here
		return 22 in self.values

	def isBust(self):
		return all(x > 21 for x in self.values)

	def canHit(self):
		return not self.isNat() and not self.isBust()

	def v(self):
		return max(x for x in self.values if x <= 21)

	def cardsDealt(self):
		"""3 means 3 or greater."""
		if self.snd is not None:
			return 2
		if self.fst is not None:
			return 1
		if self.aces or self.osum:
			return 3
		else:
			return 0

	def isDealComplete(self):
		return self.cardsDealt() >= 2

	def add(self, x):
		aces, osum, fst, snd = self.aces, self.osum, self.fst, self.snd
		num = self.cardsDealt()
		if x == 1 and not aces:
			# we don't care about any subsequent aces since we never make 2 aces worth 11
			aces += 1
		else:
			osum += (x or 10)
		if osum >= 11 and aces:
			aces = 0
			osum += 1
		if num == 0:
			fst = x
		elif num == 1:
			snd = x
		else:
			fst, snd = None, None
		return self.__class__(aces, min(23, osum), fst, snd)

	def __str__(self):
		if self.cardsDealt() <= 2:
			orig = '(' + ''.join(('A' if x == 1 else 'J' if x == 0 else str(x) if x else '?') for x in [self.fst, self.snd]) + ')'
		else:
			orig = ''
		# note: 22/23 both displayed as "XX" but this is probably less confusing since 22/23 are only different in the case of the house
		return "%s%s%s" % ('' if not self.aces else 'A' if self.aces == 1 else str(self.aces) + 'A', str(self.osum) if self.osum <= 21 else 'XX', orig)

assert H().cardsDealt() == 0
assert H().add(2).cardsDealt() == 1
assert H().add(1).cardsDealt() == 1
assert H().add(0).cardsDealt() == 1
assert H().add(1).add(0).cardsDealt() == 2
assert H().add(0).add(1).cardsDealt() == 2
assert H().add(0).add(1).add(2).cardsDealt() == 3
assert H(1, 10).v() == 21
