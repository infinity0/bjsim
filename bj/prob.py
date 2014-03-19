from fractions import Fraction
import math

"""Allow distributions to omit events totalling this probability.

This acts as a sanity check, to ensure that other optimisations you set, such
as PROB_EVENT_TOLERANCE, or using floats instead of Fractions, don't result in
wildly-inaccurate results.
"""
PROB_SPACE_TOLERANCE = 0

"""Ignore events less likely than this probability when doing ProbDist.bind.

This improves performance at the expense of accuracy, but the latter may be
acceptable for your application.
"""
PROB_EVENT_TOLERANCE = 0

def probTotal(dist):
	return sum(v[1] for v in dist)

def checkProb(dist):
	total = probTotal(dist)
	try:
		assert math.fabs(total - 1.0) <= PROB_SPACE_TOLERANCE
	except AssertionError, e:
		print math.fabs(total), dist
		raise

class ProbDist(object):
	"""Monad representing a probability distribution.

	Supports either fractions.Fraction or float as the probability.

	See the PROB_*_TOLERANCE variables for tweaks you can apply; in particular
	PROB_SPACE_TOLERANCE must be set when using floats.
	"""

	@classmethod
	def inject(cls, item):
		return cls([(item, Fraction(1))])

	def __init__(self, dist):
		checkProb(dist)
		# merge duplicates in values
		d = {}
		for item, p in dist:
			d[item] = d.get(item, 0) + p
		self.dist = sorted(d.items())

	def bind(self, f):
		"""
		@param f: f(item) -> ProbDist([(item, p)])
		"""
		newdist = []
		for item, p in self.dist:
			if p < PROB_EVENT_TOLERANCE: continue
			dist = f(item).dist
			checkProb(dist)
			newdist.extend([(v[0], p*v[1]) for v in dist])
		return self.__class__(newdist)

	def map(self, f):
		"""
		@param f: f(item) -> item2
		"""
		# short for self.bind(f compose self.__class__.inject)
		return self.__class__([(f(item), p) for item, p in self.dist])

	def filter(self, f):
		"""
		@param f: f(item) -> bool
		"""
		return self.given(f)[1]

	def given(self, f):
		"""
		Condition this distribution on the given filter.

		@param f: f(item) -> bool
		@return (p, d) where
		  p: proportion of this event space that matched
		  d: child dist, or None if no events exist that matched the filter
		"""
		g = [(item, p) for item, p in self.dist if f(item)]
		t = probTotal(g)
		return t, self.__class__([(item, p/t) for item, p in g]) if g else None

	def expect(self, f=id):
		"""
		Calculate the expected value of this distribution
		"""
		return sum(f(item)*p for item, p in self.dist)

	def __str__(self):
		return "\n".join("%.8f %s" % (p, item) for item, p in self.dist)

__f = lambda i: ProbDist([(i, 0.5), (i*2, 0.5)])
assert ProbDist.inject(1).bind(__f).bind(__f).bind(__f).dist == [(1, 0.125), (2, 0.375), (4, 0.375), (8, 0.125)]
