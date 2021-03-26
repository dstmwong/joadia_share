# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 11:42:53 2019

@author: wongm
"""
from core.engine import GameEngine, HumanPlayer
from core.environment import create_territories
from core.model import Game, MotCoy, LiftEntity, C130, MobileEntity, OPV, MRH, P8, Inf, Medic, Militia, FishingBoat, \
    Population, Side, Supply, Civilian, Phase, Surface, Entity
from core.pysimplegui_ui import JoadiaWindowApp
from ai.random_ai import RandomRedAI, RandomBlueAI

# create the game board
territories, surfaces, adjacency_matrix = create_territories("territory_def.txt")
game = Game(territories.values(), use_population_distribution=True)
engine = GameEngine(game)

Game.DO_PRINT = True

humanplayer1 = HumanPlayer("HumanPlayer1")
# humanplayer1 = RandomBlueAI("RandomBlueAI")
humanplayer1.side = Side.BLUE
humanplayer1.set_entities([MotCoy(), MotCoy(), OPV(), OPV(), C130(), P8(), Inf(), Inf(), Medic(), Medic(), MRH()])

aiplayer = RandomRedAI("RandomRedAI")
aiplayer.side = Side.RED
aiplayer.set_entities([FishingBoat(Militia()), FishingBoat(),
                       FishingBoat(Militia()), FishingBoat(),
                       FishingBoat(Militia()), FishingBoat(),
                       FishingBoat(Militia()), FishingBoat()])

engine.set_blue_player(humanplayer1)
engine.set_red_player(aiplayer)

window = JoadiaWindowApp(engine)
window.run()
