from collections import namedtuple

class Hand(namedtuple('Hand', 'ace osum fst snd')):
	"""A hand of cards.

	Attributes:
		ace:
			Whether we have an ace. (We only care about having one ace, since
			we never make two aces both worth 11).
		osum:
			Sum of all cards, excluding the ace if we have one. This value will
			be no greater than 23 (22 being special for Blackjack Switch).
		fst:
			First card dealt, or None if 0 or 3+ cards have been dealt.
		snd:
			Second card dealt, or None if 0, 1 or 3+ cards have been dealt.
	"""
	def __new__(cls, ace=False, osum=0, fst=None, snd=None):
		return super(Hand, cls).__new__(cls, bool(ace), min(23, osum), fst, snd)

	@property
	def values(self):
		return tuple(x + self.osum for x in ([1, 11] if self.ace else [0]))

	@property
	def value(self):
		"""The "best" value for this hand, i.e. closest to but leq than 21."""
		return self.osum if not self.ace else self.osum + 1 if self.osum >= 11 else self.osum + 11

	def cardsDealt(self):
		"""Number of cards dealt in this hand.

		A return-value of 3 means "3 or greater".
		"""
		if self.snd is not None:
			return 2
		if self.fst is not None:
			return 1
		if self.ace or self.osum:
			return 3
		else:
			return 0

	def isDealComplete(self):
		return self.cardsDealt() >= 2

	def isBust(self):
		return self.osum >= 22 if not self.ace else self.osum >= 21

	def isNat(self):
		# TODO: return false after switching
		return self.ace and self.osum == 10 and self.cardsDealt() == 2

	def isA17(self):
		return self.ace and self.osum == 6

	def is22(self):
		# 22s are treated specially in Blackjack Switch, so account for them here
		return self.osum == 22 if not self.ace else self.osum in (11, 21)

	def canHit(self):
		return not self.isNat() and not self.isBust()

	def add(self, x):
		"""Add a card to this hand.

		Args:
			x: The card being added. 1 is ace, and 0 is 10/J/Q/K. Other values
			represent the cards with that face value.
		"""
		ace, osum, fst, snd = self.ace, self.osum, self.fst, self.snd
		num = self.cardsDealt()
		if x == 1 and not ace:
			ace = True
		else:
			osum += (x or 10)
		if num == 0:
			fst = x
		elif num == 1:
			snd = x
		else:
			fst, snd = None, None
		return self.__class__(ace, osum, fst, snd)

	@staticmethod
	def cardsToStr(*it):
		return ''.join(('?' if x is None else 'A' if x == 1 else 'J' if x == 0 else str(x)) for x in it)

	def __str__(self):
		if self.isBust():
			return "xx"
		elif self.isNat():
			return "AJ"
		if self.cardsDealt() <= 2:
			orig = '(%s)' % Hand.cardsToStr(self.fst, self.snd)
		else:
			orig = ''
		return "%s%s%s" % ('' if not self.ace else 'A', self.osum, orig)

assert Hand().cardsDealt() == 0
assert Hand().add(2).cardsDealt() == 1
assert Hand().add(1).cardsDealt() == 1
assert Hand().add(0).cardsDealt() == 1
assert Hand().add(1).add(0).cardsDealt() == 2
assert Hand().add(0).add(1).cardsDealt() == 2
assert Hand().add(0).add(1).add(2).cardsDealt() == 3
assert Hand(1, 10).value == 21
