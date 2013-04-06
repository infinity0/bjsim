from bj.card import TotalCardState, NullCardState, PartialAJHLCardState
from bj.odds import OddsTable, testStates
from bj.rule import BJS, BJV

#print testStates(BJS, NullCardState(), PartialAJHLCardState(), TotalCardState())
#print OddsTable(TotalCardState(), BJS).checkPlayerOpts((0,6), 8, True)

print '-'*80; print "Blackjack Switch. No card counting, clean deck."
OddsTable(NullCardState(), BJS).printTable()
#OddsTable(TotalCardState(), BJS, True).printTable()

print '-'*80; print "Blackjack Switch. Partial AJHL card counting, half Js available"
OddsTable(PartialAJHLCardState(decks=BJS.defaultDecks, state=[48,0,0,0]), BJS).printTable()
#OddsTable(PartialAJHLCardState(decks=BJS.defaultDecks, state=[0,12,0,0]), BJS).printTable()
#OddsTable(PartialAJHLCardState(decks=BJS.defaultDecks, state=[0,0,48,0]), BJS).printTable()
#OddsTable(PartialAJHLCardState(decks=BJS.defaultDecks, state=[0,0,0,48]), BJS).printTable()

print '-'*80; print "Blackjack on the video machines. Perfect card counting, clean deck."
OddsTable(TotalCardState(decks=BJV.defaultDecks), BJV).printTable()

import code; code.interact(local=locals())
