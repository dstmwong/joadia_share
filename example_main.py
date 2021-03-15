# -*- coding: utf-8 -*-
"""
Created on Tue Jan 15 11:32:48 2019
This is an example of how to setup the top level main program for the JOADIA
codebase
@author: wongm
"""

from core.engine import GameEngine
from core.model import Game, MotCoy, C130, OPV, P8, Inf, Medic, Militia, FishingBoat, Side, MRH
from core.environment import create_territories
from ai.random_ai import RandomRedAI, RandomBlueAI
from ai.heuristic_ai import WorstCaseHeuristic, BestCaseHeuristic1, BestCaseHeuristic2, RandomCaseHeuristic1, \
    HillClimbingPolicy3
import time
# import random
# random.seed(1) #USE THIS FOR CONSISTENT RUN TIMES WHILST TESTING

#------------------------------------------------------------------------------
#create the game board
territories, surfaces, adjacency_matrix = create_territories("territory_def.txt")
game = Game(territories.values(), use_population_distribution=True)
engine = GameEngine(game)

#------------------------------------------------------------------------------
#creating the players and putting them on the board

#if you are subclassing from Player, override the following methods:
#place_entities
#do_dawn_phase
#do_day_phase
#do_dusk_phase
#do_night_phase ...only if you are a red player


# blueplayer = RandomBlueAI("BluePlayer")
# blueplayer = WorstCaseHeuristic()
# blueplayer = BestCaseHeuristic1()
# blueplayer = BestCaseHeuristic2()
# blueplayer = RandomCaseHeuristic1()
blueplayer = HillClimbingPolicy3()
blueplayer.side = Side.BLUE
blueplayer.set_entities([MotCoy(), MotCoy(), OPV(), 
                        OPV(), C130(), P8(), Inf(), 
                        Inf(), Medic(), Medic(), MRH()])

# redplayer = RandomRedAI("RedPlayer")
# redplayer.side = Side.RED
# redplayer.set_entities([FishingBoat(Militia()), FishingBoat(),
#                         FishingBoat(Militia()), FishingBoat(),
#                         FishingBoat(Militia()), FishingBoat(),
#                         FishingBoat(Militia()), FishingBoat()])
    
#------------------------------------------------------------------------------
       
engine.set_blue_player(blueplayer)
# engine.set_red_player(redplayer)

# run a number of games and collect some stats
num_games = 1000
total_score = 0
total_rescues = 0
best_score = -10000
best_rescues = -10000
worst_score = 10000
worst_rescues = 10000
start_time = time.time()
for i in range(0, num_games):
    # If use_population_distribution is True, this randomly resamples civilian populations each game
    for territory in engine.game.territories:
        engine.game.territories[territory].civilians.clear()
    engine.reset()
    engine.run()

    score = engine.game.get_score()
    total_score += score
    best_score = max(best_score, score)
    worst_score = min(worst_score, score)
    rescues = engine.game.rescues
    total_rescues += rescues
    best_rescues = max(best_rescues, rescues)
    worst_rescues = min(worst_rescues, rescues)

    if i % (num_games / 10) == 0:
        print("Game:", i, "Num rescues:", rescues, "Num deaths:", engine.game.deaths, "Score:", score)

duration = time.time() - start_time
average_score = total_score / num_games
average_rescues = total_rescues / num_games

print()
print("It took {:.2f} seconds to run {} games.".format(duration, num_games))
print("The best score was {}, the worst score was {} and the average score was {:.2f}.".format(
    best_score, worst_score, average_score))
print("The most rescues was {}, the least rescues was {} and the average rescues was {:.2f}.".format(
    best_rescues, worst_rescues, average_rescues))

print("{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
    type(blueplayer).__name__, best_score, average_score, worst_score, best_rescues, average_rescues, worst_rescues))
