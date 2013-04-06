import math
import sys
from collections import namedtuple
from bj.card import NullCardState, TotalCardState, PartialAJHLCardState
from bj.game import GameState, GameStateDist
from bj.hand import H
from bj.rule import BJS

def testStates(rule, *states):
	pay = []
	for cst in states:
		gsd = GameStateDist.initGame(2, cst)
		gsd = gsd.dealNewRound(cards=[9,6,8,7]).execRound([rule.playHouse, rule.playHouse])
		pay.append(gsd.expectPay(rule.pay))
	return pay

def gsdStr(gsd): return str(gsd.map(str))
def gsdStrP(gsd, h): return str(gsd.map(lambda gs: gs.simplifyCards(NullCardState).replaceHand(0, h)).map(str))
def gsdStrH(gsd): return str(gsd.map(lambda gs: gs.simplifyCards(NullCardState).simplifyHands()).map(str))
def printBlock(s): print s + '\n--------'

COLORS = {"H":'\033[42m', "S":'\033[41m', "U":'\033[45m', "D":'\033[46m\033[30m', "P":'\033[43m\033[30m'}
CEND = '\033[0m'
def oddsStr(odds):
	dodds = odds[:2]
	# since U is constant, this case isn't interesting unless it's the top strategy
	if dodds[1][0] == "U": dodds[1] = odds[2]
	text = " ".join("%s%+.2f" % p for p in dodds)

	# don't colour it in if there's not much difference
	if math.fabs(dodds[0][1]-dodds[1][1]) < 1e-4:
		return text
	else:
		return "%s%s%s" % (COLORS[dodds[0][0]], text, CEND)

class OddsTable(namedtuple('OddsTable', 'initCards rule approx2h')):
	# TODO: separate the computation from the printing

	def __new__(cls, initCards, rule, approx2h=False):
		self = super(OddsTable, cls).__new__(cls, initCards, rule, approx2h)
		return self

	def checkPlayerOpts(self, playerCards, houseCard, output=False):
		initCards = self.initCards
		rule = self.rule

		gsd0 = GameStateDist.initGame(2, initCards)
		gsd0 = gsd0.dealNewRound(cards=[playerCards[0], houseCard, playerCards[1]])
		p0 = H().add(playerCards[0]).add(playerCards[1])
		h0 = H().add(houseCard)
		if output: print initCards, repr(p0), repr(h0)
		if output: printBlock(gsdStr(gsd0))

		def payout(gsd):
			if output: printBlock(gsdStrP(gsd, h0))
			gsd = gsd.map(lambda gs: gs.turnDone().nextTurn()).execRound([rule.playHouse], 0)
			if output: printBlock(gsdStrH(gsd))
			return gsd.expectPay(rule.pay)

		gsd_h = gsd0.bind(GameState.hit)
		pay_s, pay_hs = payout(gsd0)[1], payout(gsd_h)[1]

		def approx2_hit(gsd_h):
			# second-order approximation for H, slightly more accurate but much more expensive
			# hit, must stick
			p_hn, gsd_hn = gsd_h.given(lambda gs: not gs.hand().canHit())
			# hit, option to hit again
			p_ho, gsd_ho = gsd_h.given(lambda gs: gs.hand().canHit())
			pay_hns = payout(gsd_hn)[1] if p_hn else 0.0
			pay_hos, pay_hohs = (payout(gsd_ho)[1], payout(gsd_ho.bind(GameState.hit))[1]) if p_ho else (0.0, 0.0)

			# Pay(hit) ~= Pay(hit1|couldnt_hit)*P(couldnt_hit) + max(Pay(hit2|could_hit),Pay(hit2|could_hit))*P(could_hit)
			return pay_hns*p_hn + max(pay_hos, pay_hohs)*p_ho

		pay_h = approx2_hit(gsd_h) if self.approx2h else pay_hs
		odds = {"H": pay_h, "S": pay_s}

		if "D" in rule.actions:
			odds["D"] = 2*pay_hs

		if "U" in rule.actions:
			odds["U"] = -0.5

		if "P" in rule.actions and playerCards[0] == playerCards[1]:
			splitodds = self.checkPlayerOpts((playerCards[0], None), houseCard)
			odds["P"] = 2*splitodds[0][1]

		return sorted(odds.items(), key=lambda p: p[1], reverse=True)

	def printRow(self, h):
		print h,
		sys.stdout.flush()
		for i in [2,3,4,5,6,7,8,9,0,1]:
			print '|', oddsStr(self.checkPlayerOpts(h, i)),
			sys.stdout.flush()
		print

	def printTable(self):
		for i in [9,8,7,6,5,4,3,2]: self.printRow((0,i))
		for i in [9,8,7,6,5,4,3]: self.printRow((2,i))
		for i in [9,8,7,6,5,4,3,2]: self.printRow((1,i))
		for i in [1,0,9,8,7,6,5,4,3,2]: self.printRow((i,i))
