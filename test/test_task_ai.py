# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 10:57:58 2019

@author: wongm
"""


from core.engine import GameEngine, Player
from core.model import Game, MotCoy, LiftEntity, C130, MobileEntity, OPV, MRH, P8, \
Inf, Medic, Militia, FishingBoat, Population, Side, Supply, Civilian, Phase, Surface, Entity
from core.environment import create_territories
from core.task import AStarMove, Task, TaskMotCoy, MoveCivilian

import random

               
class RandomMovementPlayer(Player):
    def __init__(self, name):
        super().__init__(name)
        self.destinations = ["T8", "T2", "T23"]
           
    def reset(self):
        super().reset()
        for entity in self.entities:
            if isinstance(entity, TaskMotCoy):
                entity.set_task(AStarMove(entity, self.engine.game.territories[random.choice(self.destinations)]))
         
    def do_dawn_phase(self, entities, territories):
        for entity in entities:
            entity.execute(Phase.DAWN)
        return True
    
    def do_day_phase(self, entities, territories):
        print("* new day phase *")
        for entity in entities:
            entity.execute(Phase.DAY)
        return True
    
    def do_dusk_phase(self, entities, territories):
        for entity in entities:
            entity.execute(Phase.DUSK)
            if isinstance(entity, TaskMotCoy):
                if entity.state() == Task.STATE_END:
                    print("--- New astar task ---")
                    entity.set_task(AStarMove(entity, self.engine.game.territories[random.choice(self.destinations)]))
        return True
    
    def do_night_phase(self, entities, territories):
        return True
    
    def on_event(self, event_name, *args):
        pass
 
class RandomMoveCivilianPlayer(Player):
    def __init__(self, name):
        super().__init__(name)
          
    def reset(self):
        super().reset()
        self.sources = [t.name for t in self.engine.game.territories.values()]
        self.destinations = ["T15"]
        for entity in self.entities:
            if isinstance(entity, TaskMotCoy):
                entity.set_task(MoveCivilian(entity, self.engine.game.territories[random.choice(self.sources)], self.engine.game.territories[random.choice(self.destinations)]))
        
    def do_dawn_phase(self, entities, territories):
        print("* dawn phase *")
        for entity in entities:
            entity.execute(Phase.DAWN)
        return True
    
    def do_day_phase(self, entities, territories):
        print("* day phase *")
        for entity in entities:
            entity.execute(Phase.DAY)
            if isinstance(entity, TaskMotCoy):
                if entity.state() == Task.STATE_END or entity.state() == Task.STATE_FAILED:
                    print("--- Begin new MoveCivilian task ---")
                    entity.set_task(MoveCivilian(entity, self.engine.game.territories[random.choice(self.sources)], self.engine.game.territories[random.choice(self.destinations)]))
        
        return True
    
    def do_dusk_phase(self, entities, territories):
        print("* dusk phase *")
        for entity in entities:
            entity.execute(Phase.DUSK)
        return True
    
    def do_night_phase(self, entities, territories):
        return True
    
    def on_event(self, event_name, *args):
        pass
    
    
def test1():
    """
    Calculation of Astar path for AI
    This test is asking for a path from a MotCoy's current position in T15 to 
    territory T5
    """
    print("Running test1")
    #create the game board
    territories, surfaces, adjacency_matrix = create_territories("../territory_def.txt")
    game = Game(territories.values())
    engine = GameEngine(game)

    aimotcoy = TaskMotCoy()
    rlplayer = Player("Player")
    rlplayer.set_entities([aimotcoy])
    rlplayer.side = Side.BLUE
    
    engine.add_player(rlplayer)
    engine.reset()
    
    aimotcoy.add_task(AStarMove(aimotcoy, territories["T5"]))
    aimotcoy.execute(Phase.DAWN)
 
    
def test2():
    """
    Calculation of Astar path for AI
    This test is asking for a path from a MotCoy's current position in T15 to 
    a territory with no path T20
    """
    print("Running test2")
    #create the game board
    territories, surfaces, adjacency_matrix = create_territories("../territory_def.txt")
    game = Game(territories.values())
    engine = GameEngine(game)

    aimotcoy = TaskMotCoy()
    rlplayer = Player("Player")
    rlplayer.set_entities([aimotcoy])
    rlplayer.side = Side.BLUE
    
    engine.add_player(rlplayer)
    engine.reset()
    
    aimotcoy.add_task(AStarMove(aimotcoy, territories["T20"]))
    aimotcoy.execute(Phase.DAWN)

  
def test3():
    """
    RandomMovementPlayer will randomly pick target destination for the AIMotCoy
    to move to. AIMotCoy will utilise the AStarMove task to perform the move
    function
    """
    print("Running test3")
    #create the game board
    territories, surfaces, adjacency_matrix = create_territories("./territory_def.txt")
    game = Game(territories.values())
    engine = GameEngine(game)

    aimotcoy = TaskMotCoy()
    rlplayer = RandomMovementPlayer("RandomMovementPlayer")
    rlplayer.set_entities([aimotcoy])
    rlplayer.side = Side.BLUE
    
    engine.add_player(rlplayer)
    engine.game.add_listener(rlplayer)
    engine.reset()
    
    engine.run()
    
def test4():
    print("Running test4:Random multiple Astar calculated paths")
    #create the game board
    territories, surfaces, adjacency_matrix = create_territories("./territory_def.txt")
    game = Game(territories.values())
    engine = GameEngine(game)

    aimotcoy = TaskMotCoy()
    rlplayer = RandomMovementPlayer("RandomMovementPlayer")
    rlplayer.set_entities([aimotcoy])
    rlplayer.side = Side.BLUE
    
    engine.add_player(rlplayer)
    engine.game.add_listener(rlplayer)
    
    from core.pysimplegui_ui import JoadiaWindowApp
    window = JoadiaWindowApp(engine)
    window.run()
    
def test5():
    print("Running test4:Random collection of civilians and dropoffs")
    #create the game board
    territories, surfaces, adjacency_matrix = create_territories("./territory_def.txt")
    game = Game(territories.values())
    engine = GameEngine(game)

    aimotcoy = TaskMotCoy()
    rlplayer = RandomMoveCivilianPlayer("RandomMoveCivilianPlayer")
    rlplayer.set_entities([aimotcoy])
    rlplayer.side = Side.BLUE
    
    engine.add_player(rlplayer)
    engine.game.add_listener(rlplayer)
    engine.reset()
    engine.run()
    
    from core.pysimplegui_ui import JoadiaWindowApp
    window = JoadiaWindowApp(engine)
    window.run()
    

test5()