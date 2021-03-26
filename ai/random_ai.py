# -*- coding: utf-8 -*-
"""
Created on Fri Oct 19 10:41:30 2018

@author: wongm
"""
from core.model import Side, MobileEntity, LiftEntity, C130, OPV, Militia, \
Population, FishingBoat, Medic, Inf, Civilian, Supply, P8, MotCoy, Game

import core.model 
from core.engine import Player, TimerPlayer
import random

DEBUG=False

def do_random_movement(entities, player):
    for entity in entities:
        if isinstance(entity, MobileEntity):
            while True:
                land_connections, sea_connections, air_connections = entity.get_valid_moves()
                
                #while we can still make valid moves
                if land_connections == sea_connections == air_connections == []:
                    break
                if entity.move_land and land_connections != []:
                    land = random.choice(land_connections)
                    player.execute_move(entity.name, "move", land.name)
                elif entity.move_air and air_connections != []:
                    air = random.choice(air_connections)
                    player.execute_move(entity.name, "move", air.name)
                elif entity.move_water and sea_connections != []:
                    sea = random.choice(sea_connections)
                    player.execute_move(entity.name, "move", sea.name)
                    
def do_motcoy_random_movement(entity, player):
    if isinstance(entity, MotCoy):
        while True:
            land_connections, sea_connections, air_connections = entity.get_valid_moves()
                
            #while we can still make valid moves
            if land_connections == sea_connections == air_connections == []:
                break
             
            #randomly do isr on the move on the territory that they are currently on
            if random.randint(0, 1) == 1:
                if not entity.territory.blue_revealed:
                    player.execute_move(entity.name, "do isr", entity.territory.name)
            #else randomly select the next territory to move to next
            else:
                if entity.move_land and land_connections != []:
                    land = random.choice(land_connections)
                    player.execute_move(entity.name, "move", land.name)
                
#TODO refactor to use execute_move instead of calling function directly                    
def do_deterministic_movement(entities):
    for entity in entities:
        if isinstance(entity, MobileEntity):
            while True:
                land_connections, sea_connections, air_connections = entity.get_valid_moves()
                #while we can still make valid moves
                if land_connections == sea_connections == air_connections == []:
                    break
                if entity.move_land and land_connections != []:
                    land = land_connections[0]
                    entity.move(land)
                elif entity.move_air and air_connections != []:
                    air = air_connections[0]
                    entity.move(air)
                elif entity.move_water and sea_connections != []:
                    sea = sea_connections[0]
                    entity.move(sea)
                    
#==============================================================================        
 
class RandomBlueAI(Player):
    def __init__(self, name):
        super().__init__(name)
        self.side = Side.BLUE
        self.timer_player = TimerPlayer(self.name)
        pass
    
    def place_entities(self, territories):
        #override this method to place entities in alternate territories
        super().place_entities(territories)
                  
    def do_dawn_phase(self, entities, territories):
        if Game.DO_PRINT:
            print("")
            print("--*", self.name, "doing dawn phase *--")
            
        for entity in entities:
            #if we are MOTCOY, OPV or MRH
            if isinstance(entity, LiftEntity):
                if entity.is_empty():
                    #decide if we want to lift supplies or passengers
                    if random.randint(0, 1) == 1:
                        entity.set_carry_mode(LiftEntity.SUPPLY)
                    else:
                        entity.set_carry_mode(LiftEntity.PAX)
                
                #next figure out how many we want to lift
                if entity.carry_mode == LiftEntity.PAX:
                    #if we have room to lift, randomly lift either a civilian or a military mobile entity
                    if not entity.is_full() and entity.territory != None and entity.territory.state != Population.UNREST:
                        if random.randint(0, 1) == 0:
                            liftables = entity.get_liftable_civilians()
                        else:
                            liftables = entity.get_liftable_mobile_entities()
                        if liftables != []:
                            super().execute_move(entity.name, "lift PAX", liftables[0].name)
        
                elif entity.carry_mode == LiftEntity.SUPPLY:
                    if not entity.is_full() and entity.territory != None and entity.territory.num_supplies() != 0:
                        super().execute_move(entity.name, "lift supply", entity.supply_capacity)
                    
            elif isinstance(entity, C130):
                if entity.cargo == []:
                    if not super().execute_move(entity.name, "load civ"):
                        if not super().execute_move(entity.name, "load max supplies"):
                            liftable_entities = entity.get_liftable_mobile_entities()
                            if liftable_entities != []:
                                super().execute_move(entity.name, "load units", (random.choice(liftable_entities)).name)
        return True               
        

               
    def do_day_phase(self, entities, territories):
        if Game.DO_PRINT:
            print("")
            print("--*", self.name, "doing day phase *--")
         
        #every entity that is not a C130, P8 or a MotCoy just does random movement 
        do_random_movement([e for e in entities if not isinstance(e, C130) and not isinstance(e, P8) and not isinstance(e, MotCoy)], self)
        
        #day phase actions for MotCoys
        MotCoys = [entity for entity in entities if isinstance(entity, MotCoy)]
        for entity in MotCoys:
            do_motcoy_random_movement(entity, self)
        
        #day phase actions for C130s
        C130s = [entity for entity in entities if isinstance(entity, C130)]
        for entity in C130s:
            if entity.cargo != []:
                if isinstance(entity.cargo[0], Civilian):
                    super().execute_move(entity.name, "evacuate")
                elif isinstance(entity.cargo[0], Supply):
                    while len(entity.cargo) != 0:
                        super().execute_move(entity.name, "airdrop supplies", (random.choice(list(territories.values()))).name)
                elif isinstance(entity.cargo[0], MobileEntity):
                    super().execute_move(entity.name, "lift units")
                    
        #day phase actions for P8s           
        P8s = [entity for entity in entities if isinstance(entity, P8)]
        for entity in P8s:
            #if random.randint(0, 1) == 1:
                
            #select a random fishing boat to identify
            fishing_boats = [e for e in self.engine.game.entities_on_board.values() if isinstance(e, FishingBoat)]
            if fishing_boats != []:
                boat = random.choice(fishing_boats)
                super().execute_move(entity.name, "identify", boat.name)
            #else:
            #    do_random_movement([entity], self)
                
        return True
        
    
    
    def _do_drop(self, entity):
        #if we are lifting passengers
        if entity.carry_mode == LiftEntity.PAX:
            while (len(entity.cargo) != 0):
                if random.randint(0, 1) == 1:
                    super().execute_move(entity.name, "drop PAX", entity.cargo[0].name)
            
        #if we are lifting supplies
        elif entity.carry_mode == LiftEntity.SUPPLY:
            if random.randint(0, 1) == 1:
                super().execute_move(entity.name, "drop supplies", entity.current_load())
                
  
    def do_dusk_phase(self, entities, territories):
        if Game.DO_PRINT:
            print("")
            print("--*", self.name, "doing dusk phase *--")
        for entity in entities:
            #if we are MOTCOY, OPV or MRH
            if isinstance(entity, LiftEntity):
                self._do_drop(entity)
#                #the OPV can only choose to unload cargo or interdict fishing boats
#                if isinstance(entity, OPV):
#                    if entity.cargo != []:
#                        self._do_drop(entity)
#                    else:
#                        entity.interdict()
#                else:
#                    self._do_drop(entity)
           
        return True
    

#==============================================================================

class RandomRedAI(Player):
    def __init__(self, name):
        super().__init__(name)
        self.side = Side.RED
        
    def place_entities(self, territories):
        #red does not put any entities on territories in the beginning
        pass

    def do_night_phase(self, entities, territories):
        if Game.DO_PRINT:
            print("")
            print("--*", self.name, "doing night phase *--")
        
        #random move all opfor entities
        do_random_movement(entities, self)
    
        #or perform some militia action 
        for opfor in entities:
            if isinstance(opfor, Militia):
                if opfor.territory.size != Population.NONE:
                    rand_choice = random.randint(0,2)
                    if rand_choice == 0:
                        super().execute_move(opfor.name, "sabotage supply")
                        
                    elif rand_choice == 1:
                        super().execute_move(opfor.name, "injure population", 2)
                        
                    elif rand_choice == 2:
                        super().execute_move(opfor.name, "cause unrest")
                        
            elif isinstance(opfor, FishingBoat):
                #randomly choose to deploy a militia if available
                if opfor.militia != None:
                    super().execute_move(opfor.name, "deploy militia")
                
        
        #put up to two fishing boats per turn into the game board
        to_be_placed = [opfor for opfor in self.entities if opfor.surface == None and opfor.alive == True]
        
        if len(to_be_placed) != 0:
            random_opfor = random.choice(to_be_placed)
            if random.randint(0, 1) == 1:
                super().execute_move(random_opfor.name, "launch boat", "T8")
                #print(random_opfor.name + " was launched at T8")
            else:
                super().execute_move(random_opfor.name, "launch boat", "T17")
                #print(random_opfor.name + " was launched at T17")
    
        return True
    
#==============================================================================

class CyclingRedAI(Player):
    """
    A version of RedAI that will deterministically cycle through actions 
    available
    """
    def __init__(self, name):
        super().__init__(name)
        self.side = Side.RED
        self.militia_action = 0
        self.fishing_boat_action = 0
        
        

    def do_night_phase(self, entities, territories):
        if Game.DO_PRINT:
            print("")
            print("--*", self.name, "doing night phase *--")
        #random move all opfor entities
        do_deterministic_movement(entities)
    
        #or perform some militia action 
        for opfor in entities:
            if isinstance(opfor, Militia):
                if opfor.territory.size != Population.NONE:
                    if self.militia_action == 0:
                        opfor.sabotage_supply()
                    elif self.militia_action == 1:
                        opfor.injure_population(2)
                    elif self.militia_action == 2:
                        opfor.cause_unrest()
                        
                    self.militia_action += 1
                    if self.militia_action > 2:
                        self.militia_action = 0
            elif isinstance(opfor, FishingBoat):
                if opfor.militia != None and opfor.territory != None:
                    opfor.deploy_militia(opfor.territory)
                
        
        #put up to two new entities per turn
        #if random.randint(0, 1) == 1:
        to_be_placed = [opfor for opfor in self.entities if opfor.surface == None 
                        and opfor.alive == True and not opfor in self.engine.game.entities.values()]
        
        if len(to_be_placed) != 0:
            fishing_boat = to_be_placed[0]
            if self.fishing_boat_action == 1:
                fishing_boat.place(territories["T11"].seas[0])
                self.fishing_boat_action = 0
            elif self.fishing_boat_action == 0:
                fishing_boat.place(territories["T21"].seas[0])
                self.fishing_boat_action = 1

            if Game.DO_PRINT: 
                print("Linksky has launched a fishing boat!")
    
        return True