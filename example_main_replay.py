# -*- coding: utf-8 -*-
"""
Created on Tue Jan 15 11:32:48 2019
This is an example showing randomised AI performing moves, moves being exported
out to file and then and being replayed via the visualiser
@author: wongm
"""

from core.engine import GameEngine, Player, TimerPlayer, HumanPlayer
from core.model import Game, MotCoy, LiftEntity, C130, MobileEntity, OPV, MRH, P8, Inf, Medic, Militia, FishingBoat, Population, Side, Supply, Civilian, Phase
from core.environment import create_territories
from ai.random_ai import RandomRedAI, RandomBlueAI, CyclingRedAI
from ai.beamSearch_ai import BeamSearchBlueAI
from core.pysimplegui_ui import JoadiaWindowApp


#------------------------------------------------------------------------------
#create the game board
territories, surfaces, adjacency_matrix = create_territories("territory_def.txt")
game = Game(territories.values(), use_population_distribution=True)
engine = GameEngine(game)

#------------------------------------------------------------------------------
#creating the players and putting them on the board

blueplayer = RandomBlueAI("BluePlayer")
blueplayer.side = Side.BLUE
blueplayer.set_entities([MotCoy(), MotCoy(), OPV(), 
                        OPV(), C130(), P8(), Inf(), 
                        Inf(), Medic(), Medic()]) 

redplayer = RandomRedAI("RedPlayer")
redplayer.side = Side.RED
redplayer.set_entities([FishingBoat(Militia()), FishingBoat(), 
                        FishingBoat(Militia()), FishingBoat(), 
                        FishingBoat(Militia()), FishingBoat(), 
                        FishingBoat(Militia()), FishingBoat()])
    
#------------------------------------------------------------------------------
       
engine.set_blue_player(blueplayer)
engine.set_red_player(redplayer)

engine.reset()
engine.run()

engine.save_state_to_file("./replays/example_replay.json")
  
window = JoadiaWindowApp(engine)
window.load_replay_file("./replays/example_replay.json")
window.run()

    
    
