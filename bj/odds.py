import logging
import math
import sys

from collections import namedtuple
from bj.card import NullCardState, TotalCardState, PartialAJHLCardState
from bj.game import GameState, GameStateDist
from bj.hand import Hand
from bj.rule import BJS


class lazyStr(namedtuple("lazyStr", "f")):
	def __str__(self):
		return str(self.f())


COLORS = {"H":'\033[42m', "S":'\033[41m', "U":'\033[45m', "D":'\033[46m\033[30m', "P":'\033[43m\033[30m'}
CEND = '\033[0m'
def oddsStr(odds):
	dodds = odds[:2]
	# since U is constant, this case isn't interesting unless it's the top strategy
	if len(odds) > 2 and dodds[1][0] == "U":
		dodds[1] = odds[2]

	text = " ".join("%s%+.2f" % p for p in dodds).ljust(13, " ")
	# don't colour it in if there's not much difference
	if len(dodds) > 1 and math.fabs(dodds[0][1]-dodds[1][1]) < 1e-4:
		return text
	else:
		return "%s%s%s" % (COLORS[dodds[0][0]], text, CEND)


class OddsCalculator(namedtuple('OddsCalculator', 'initCards rule approx2h')):

	def expectHousePay(self, h0, gsd):
		logging.debug("-------- house initial hand vs player hands\n%s",
			lazyStr(lambda: gsd.map(lambda gs: gs.replaceDecks(NullCardState()).replaceHand(0, h0)).map(str)))
		gsd = gsd.map(GameState.turnDoneNext).execRound([self.rule.playHouse], 0)
		logging.debug("-------- house hand vs player end results\n%s",
			lazyStr(lambda: gsd.map(lambda gs: gs.replaceDecks(NullCardState()).describeHands()).map(str)))
		return gsd.expectPay(self.rule.pay)

	def calculateOdds(self, playerCard0, houseCard, playerCard1=None):
		initCards = self.initCards
		rule = self.rule

		gsd0 = GameStateDist.initGame(2, initCards)
		gsd0 = gsd0.dealNewRound(cards=[playerCard0, houseCard, playerCard1])
		p0 = Hand().add(playerCard0).add(playerCard1)
		h0 = Hand().add(houseCard)
		logging.debug("-------- initial hands\nCards=%s\nPlayer=%s House=%s\n%s",
			initCards, repr(p0), repr(h0), lazyStr(lambda: gsd0.map(str)))

		payout = lambda gsd: self.expectHousePay(h0, gsd)
		odds = {}

		if "U" in rule.actions:
			odds["U"] = -0.5

		if "S" in rule.actions:
			pay_s = payout(gsd0)[1]
			odds["S"] = pay_s

		if "H" in rule.actions and p0.canHit():
			gsd_h = gsd0.bind(GameState.hit)
			pay_hs = payout(gsd_h)[1]

			if self.approx2h:
				# second-order approximation for H, slightly more accurate but much more expensive
				# hit, must stick
				p_hn, gsd_hn = gsd_h.given(lambda gs: not gs.currentHand().canHit())
				# hit, option to hit again
				p_ho, gsd_ho = gsd_h.given(lambda gs: gs.currentHand().canHit())
				pay_hns = payout(gsd_hn)[1] if p_hn else 0.0
				pay_hos, pay_hohs = (payout(gsd_ho)[1], payout(gsd_ho.bind(GameState.hit))[1]) if p_ho else (0.0, 0.0)

				# Pay(hit) ~= Pay(hit1|couldnt_hit)*P(couldnt_hit) + max(Pay(hit2|could_hit),Pay(hit2|could_hit))*P(could_hit)
				pay_h = pay_hns * p_hn + max(pay_hos, pay_hohs) * p_ho
			else:
				pay_h = pay_hs

			odds["H"] = pay_h

		if "D" in rule.actions and "H" in odds:
			odds["D"] = 2 * odds["H"]

		if "P" in rule.actions and playerCard0 == playerCard1:
			splitodds = self.calculateOdds(playerCard0, houseCard)
			odds["P"] = 2 * splitodds[0][1]

		return sorted(odds.items(), key=lambda p: p[1], reverse=True)

	def printRow(self, h0, h1, fp=sys.stdout):
		print >>fp, Hand.cardsToStr(h0, h1),
		fp.flush()
		for i in [2,3,4,5,6,7,8,9,0,1]:
			print >>fp, '|', oddsStr(self.calculateOdds(h0, i, h1)),
			fp.flush()
		print >>fp

	def printTable(self, fp=sys.stdout):
		divider = "---+-" + "-+-".join("-"*13 for i in [2,3,4,5,6,7,8,9,0,1])
		print >>fp, "P\H|", " | ".join(Hand.cardsToStr(i).rjust(13, " ") for i in [2,3,4,5,6,7,8,9,0,1])
		print >>fp, divider
		for i in [0,9,8,7,6,5,4,3,2]: self.printRow(1, i, fp)
		print >>fp, divider
		for i in [9,8,7,6,5,4,3,2]: self.printRow(0, i, fp)
		for i in [9,8,7,6,5,4,3]: self.printRow(2, i, fp)
		print >>fp, divider
		for i in [1,0,9,8,7,6,5,4,3,2]: self.printRow(i, i, fp)
