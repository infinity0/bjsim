import math

# allow distributions to omit events totalling this probability
PROB_SPACE_TOLERANCE = 1e-6
# ProbDist.bind will discard source events with this probability
PROB_EVENT_TOLERANCE = 1e-10

def probTotal(dist):
	return sum(v[1] for v in dist)

def checkProb(dist):
	try:
		assert math.fabs(probTotal(dist) - 1.0) < PROB_SPACE_TOLERANCE
	except AssertionError, e:
		print math.fabs(probTotal(dist)), dist
		raise

class ProbDist(object):
	"""Monad representing a probability distribution."""

	@classmethod
	def inject(cls, item):
		return cls([(item, 1.0)])

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
