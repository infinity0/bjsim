#!/usr/bin/pypy

import argparse
import ast
import logging
import sys
import textwrap

from bj.card import CardState
from bj.odds import OddsCalculator
from bj.prob import add_module_opts as add_module_opts__bj_prob
from bj.rule import BJ, BJS, BJV

import bj.prob

def main(argv):
	parser = argparse.ArgumentParser(
		formatter_class=argparse.RawDescriptionHelpFormatter,
		description=textwrap.dedent("""\
		Calculate optimal strategies for various blackjack games.

		Examples:

		  # Strategy table for standard Blackjack, no card counting.
		  $ bj.py

		  # Strategy table for Blackjack Switch. Partial AJHL card counting, half Js available.
		  $ bj.py --rule BJS --count PartialAJHLCardState --card-state [48,0,0,0]

		  # Strategy table for Blackjack on the video machines. Perfect card counting.
		  $ bj.py --rule BJV --count TotalCardState

		  # Exact odds for (10, 6) vs House 8, for standard Blackjack.
		  $ bj.py --count TotalCardState 086

		See README for more details.

		If calculations take too long, you can try setting `--prob-event-tolerance 1e-6
		--prob-event-tolerance 1e-2` which shouldn't affect results much. If you only
		want to get a "general sense" of what a strategy looks like, you can try
		`--prob-event-tolerance 1e-4 --prob-event-tolerance 1e-1` but a few results
		will be visibly different from the actual optimal ones.
		"""))
	parser.add_argument(
		"hands", help="3-char string describing the initial hand to calculate "
		"odds for. Each char is a digit for the card with that face value, "
		"except 0 means 10/J/Q/K and 1 means Ace. Cards are given in the order "
		"of being dealt, i.e. [player,house,player]. If omitted, we calculate "
		"optimal strategies for a representative set of initial hands.",
		nargs="*", type=lambda s: map(int, list(s.ljust(3,"X")[:3])))
	parser.add_argument(
		"--rule", help="Blackjack rule to play with. Default: %(default)s",
		default="BJ", choices=["BJ", "BJS", "BJV"])
	parser.add_argument(
		"--count", help="Method of card counting. Default: %(default)s",
		default="NullCardState", choices=[c.__name__ for c in CardState.__subclasses__()])
	parser.add_argument(
		"--card-decks", help="Number of decks in play. Default: whatever the "
		"default is for the rule being played.",
		default=None, type=int)
	parser.add_argument(
		"--card-state", help="Initial state of cards, as a python expression "
		"that is passed to the card-state constructor. Default: %(default)s",
		default=None, type=ast.literal_eval)
	parser.add_argument(
		"--approx2h", help="Use 2nd-order calculation, which is slightly more "
		"accurate but much more expensive to calculate. Default: %(default)s",
		default=False, action="store_true")
	parser.add_argument(
		"--verbose", help="Show more output. Default: %(default)s",
		default=False, action="store_true")
	parser.add_argument(
		"--repl", help="Drop to the python REPL after calculations are done.",
		default=False, action="store_true")
	add_module_opts__bj_prob(parser)
	args = parser.parse_args(argv)

	if args.verbose:
		logging.getLogger().setLevel(logging.DEBUG)

	rule = getattr(bj.rule, args.rule)
	cardtype = getattr(bj.card, args.count)
	cards = cardtype(decks=args.card_decks or rule.defaultDecks, state=args.card_state)

	calc = OddsCalculator(cards, rule, approx2h=args.approx2h)
	print "%s; initial card state = %s." % (rule.name, cards)

	if args.hands:
		for h in args.hands:
			print "(%s, %s) vs House %s: %s" % (h[0], h[2], h[1], calc.calculateOdds(*h))
	else:
		calc.printTable()

	if args.repl:
		import code
		code.interact(local=locals())

if __name__ == '__main__':
	sys.exit(main(sys.argv[1:]))
