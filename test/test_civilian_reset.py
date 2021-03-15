# -*- coding: utf-8 -*-
"""
Created on Tue Jan 15 11:32:48 2019
These are a series of test designed to uncover issues in the refactor process of
converting civilians into unique entities in the JOADIA wargame
@author: wongm
"""

from core.engine import GameEngine, Player, TimerPlayer, HumanPlayer
from core.model import Game, MotCoy, LiftEntity, C130, MobileEntity, OPV, MRH, P8, Inf, Medic, Militia, FishingBoat, Population, Side, Supply, Civilian, Phase
from core.environment import create_territories
from ai.random_ai import RandomRedAI, RandomBlueAI, CyclingRedAI


#------------------------------------------------------------------------------
#create the game board
territories, surfaces, adjacency_matrix = create_territories("territory_def.txt")
game = Game(territories.values())
engine = GameEngine(game)

motcoy = MotCoy()
c130 = C130()

#humanplayer1 = HumanPlayer("HumanPlayer1")
#humanplayer1 = RandomBlueAI("RandomBlueAI")
#humanplayer1.side = Side.BLUE
#humanplayer1.set_entities([motcoy, c130])
#engine.add_player(humanplayer1)

engine.reset()

t = engine.game.territories["T14"]        

l14_loc = engine.game.get_surface("L14")
l15_loc = engine.game.get_surface("L15")

c130.place(engine.game.get_surface("A15"))
c130.apod_territories.append(territories["T9"])
c130.apod_territories.append(territories["T15"])

#------------------------------------------------------------------------------
print("***")
print("-- test moving civilian --")
motcoy.move(l14_loc)
civ = motcoy.get_liftable_civilians()[0]
print("territory of civilian",  civ.id, "before move", civ.territory.name)
motcoy.lift_pax(civ)
motcoy.move(l15_loc)
motcoy.drop_pax(civ)
print("territory of civilian", civ.id, "after move", civ.territory.name)

#after the reset, civilian territory should go back to the T14
engine.reset()
print("territory and surface of civilian", civ.id, "after move AND reset", civ.territory.name, civ.surface.name)

#test setting territory to None
civ.territory = None
engine.reset()
print("territory and surface of civilian", civ.id, "after set to None AND reset", civ.territory.name, civ.surface.name)

#------------------------------------------------------------------------------
#test evacuating civilian
print("***")
print("-- test evacuting civilian --")
ret = motcoy.move(l14_loc)
civ = motcoy.get_liftable_civilians()[0]
print("territory of civilian", civ.id, "before move", civ.territory.name)
motcoy.lift_pax(civ)
motcoy.move(l15_loc)
motcoy.drop_pax(civ)
print("territory of civilian", civ.id, "after move", civ.territory.name)

c130.load_civilians()
c130.evacuate_civilians()
print("territory of civilian", civ.id, "after c130 evacuate", civ.territory)

#------------------------------------------------------------------------------

#test random movement of civilians to different territories using the territory
#add_civilian and
print("***")
print("-- test random movement of civilians -- ")

territories = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"]

import random

for i in range(0, 5):
    rand_territory = random.choice(list(engine.game.territories.values()))
    if rand_territory.get_civilians() != []:
        print("BEFORE ADD", [civ.name for civ in rand_territory.get_civilians()])
        
        rand_civilian = random.choice(rand_territory.get_civilians())
        print("civilian id", rand_civilian.name, "civilian territory", rand_civilian.territory.name)
        
        target_territory = random.choice(list(engine.game.territories.values()))
        print("target territory", target_territory.name)
        
        target_territory.add_civilian(rand_civilian)
        print("civilian id", rand_civilian.id, "civilian territory", rand_civilian.territory.name)
        
        print("AFTER ADD", [civ.name for civ in rand_territory.get_civilians()])
        print(rand_civilian.territory.name == target_territory.name)
    else:
        print("No civilians in", rand_territory.name)

#------------------------------------------------------------------------------

#test random movement of civilians to different territories using the territory
#add_civilian but this time we set territories to unrest
print("***")
print("-- test random movement of civilians with unrest-- ")

territories = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"]

import random

for i in range(0, 1):
    rand_territory = random.choice(list(engine.game.territories.values()))
    if rand_territory.get_civilians() != []:
        rand_territory.state = Population.UNREST
        
        print("BEFORE ADD", [civ.name for civ in rand_territory.get_civilians()])
        
        rand_civilian = random.choice(rand_territory.get_civilians())
        print("civilian id", rand_civilian.name, "civilian territory", rand_civilian.territory.name)
        
        target_territory = random.choice(list(engine.game.territories.values()))
        print("target territory", target_territory.name)
        
        #telemove the motcoy so we can lift the civilian
        #engine.game.move_entity(motcoy, motcoy.surface, rand_territory.lands[0])
        print("motcoy territory", motcoy.territory.name)
        
        motcoy.lift_pax(rand_civilian)
        #should fail to lift and be empty here
        print("motcoy cargo", [cargo.name for cargo in motcoy.cargo])
        
        engine.game.move_entity(motcoy, motcoy.surface, target_territory.lands[0])
        motcoy.drop_pax(rand_civilian)
        
        print("AFTER ADD", [civ.name for civ in rand_territory.get_civilians()])
        print(rand_civilian.territory.name != target_territory.name)
    else:
        print("No civilians in", rand_territory.name)
    
    
#------------------------------------------------------------------------------
#test removing healthy civilians
print("***")
print("-- test random removal of healthy and injured civilians-- ")

territories = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"]

import random

for i in range(0, 1):
    rand_territory = random.choice(list(engine.game.territories.values()))
    print("BEFORE REMOVE", [civ.state for civ in rand_territory.get_civilians()])
    rand_territory.remove_healthy_civilian()
    print("AFTER REMOVE HEALTHY", [civ.state for civ in rand_territory.get_civilians()])
    rand_territory.remove_injured_civilian()
    print("AFTER REMOVE INJURED", [civ.state for civ in rand_territory.get_civilians()])
    
#------------------------------------------------------------------------------
print("***")
print("-- test checking for civilians with None territories after reset -- ")

for i in range(0, 10):
    engine.reset()
    for t in engine.game.territories.values():
        for c in t.get_civilians():
            if c.territory == None:
                print(c.name, "has no territory")
    

