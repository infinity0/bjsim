Blackjack odds calculator
=========================

See ``--help`` for an overview of options.

When printing strategy tables, the columns are the dealer's first card and go
2-9,J,A. Rows are your cards; 1 represents ace and 0 represents 10,J,Q,K
(sometimes collectively referred to as Js in the rest of these docs/code).

You may take the rows for (0,*) and (2,*) to represent approximate strategy for
any hard (no-A) hand totalling the same amount (e.g. (0,9) = any hand totalling
19); this is not strictly correct but is much much faster to calculate. I may
fix this in the future, or at least give the user an option to sacrifice speed
for correctness.

Red
	Stand
Green
	Hit
Yellow
	Split
Cyan
	Double (double your bet, hit exactly once then stand)
Purple
	Surrender (lose half your bet)

Note that in some games, not all of these actions are allowed, and so won't
show up in the final table.

Accuracy
--------

This program will undoubtably generate tables that differ from other
strategy-tables you might find online. Hopefully these discrepancies are minor;
but possible explanations for them are:

- Perhaps you input preconditions into this program that are different from
  what the other table used.

- This program is not perfect and I did approximate certain things so the
  computation finishes in a reasonable amount of time.

- The other table is at fault; most online tables just give you a bunch of
  commands and you have to "trust them" - they could very well be incorrect
  rather than this program.

Disclaimer
----------

Should you wish to use this program for something stupid such as trying to win
any actual games of blackjack, please see LICENSE for a full legal disclaimer.
