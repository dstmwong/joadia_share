# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 11:06:18 2018

@author: wongm
"""

import random
import math


#change these settings to set the default number of civilians spawned
MAX_CIV_CITY = 6
MIN_CIV_CITY = 4
MAX_CIV_TOWN = 4
MIN_CIV_TOWN = 2
MAX_CIV_VILLAGE = 2
MIN_CIV_VILLAGE = 1

MAX_INJURED = 3
MIN_INJURED = 0

DO_CONSUMPTION_PHASE = True

DEBUG = True
DEBUG_MOVEMENT = False

DO_PRINT = False


class Game:
    #how many supply cubes the fob gets on resupply
    INITIAL_RESUPPLY_NUM = 20
    RESUPPLY_NUM = 15
    
    def __init__(self, in_territories=[], use_population_distribution=True, civ_city=MAX_CIV_CITY,
                 civ_town=MAX_CIV_TOWN, civ_village=MAX_CIV_VILLAGE, civ_injured=MAX_INJURED):
        self.use_population_distribution = use_population_distribution
        self.civ_city = civ_city
        self.civ_town = civ_town
        self.civ_village = civ_village
        self.civ_injured = civ_injured
        self.turn_num = 0
        self.phase = Phase.DAWN
        self.deaths = 0
        self.rescues = 0
        self.territories = {}
        self.surfaces = {}

        #PERFORMANCE IMPROVEMENT
        #Use of dictionary for listeners will eliminate the calls to event handlers that do not handle particular events 
        self.listeners_dict = {}
        
        #register all territories and surfaces
        for t in in_territories:
            t.game = self
            self.territories[t.name] = t
            for surface in t.get_all_surfaces():
                self.surfaces[surface.name] = surface
        
        self.entities = {}
        self.entities_on_board = {}
   
     
    def get_surface(self, surface_name):
        prefix_char = surface_name[0]
        territory_num = surface_name[1:].split("_")[0]
        
        t_name = "T" + territory_num
        if t_name in self.territories.keys():
            territory = self.territories[t_name]
            if territory != None:
                if prefix_char == "L":
                    for land in territory.lands:
                        if land.name == surface_name:
                            return land
                    return territory.lands[0]
                elif prefix_char == "S":
                    for sea in territory.seas:
                        if sea.name == surface_name:
                            return sea
                elif prefix_char == "A":
                    for air in territory.airs:
                        if air.name == surface_name:
                            return air
        return None
        
    
    def copy(self):
        """
        creates a copy of the game at the state at which this method was called
        TODO: Incomplete and untested. Don't use it yet! 
        """
        copied_territories = {}
        for t in self.territories.values():
            copied_territories[t.name] = t.copy()
            
        copied_game = Game(copied_territories)
        copied_game.turn_num = self.turn_num
        copied_game.phase = self.phase
        copied_game.deaths = self.deaths
        copied_game.rescues = self.rescues
        copied_game.use_population_distribution = self.use_population_distribution
        
        return copied_game
        
        
    def reset(self):
        if DO_PRINT:
            print("Game:reset")
        
        self.turn_num = 0
        self.phase = Phase.DAWN
        self.deaths = 0
        self.rescues = 0
        
         #clear all entities from the game board
        self.entities.clear()
        self.entities_on_board.clear()
        
        #clear all supplies and civilians and rebuild the original population
        for t in self.territories.values():
            t.reset()

        #TODO: surfaces?
             
        #the initial supply cubes in the FOB
        self.strat_resupply(Game.INITIAL_RESUPPLY_NUM)
        
        #all fob areas have been revealed
        for t in self.territories.values():
            if t.has_pod(POD.SEA) or t.has_pod(POD.AIR):
                t.blue_revealed = True

    def replayInit(self, givenTerritories):
        self.turn_num = 0
        self.phase = Phase.DAWN
        self.deaths = 0
        self.rescues = 0
        
        #clear all entities from the game board

        self.entities.clear()
        self.entities_on_board.clear()

        for t in givenTerritories:
            if t['Name'] != None:
                num_healthy = 0
                num_injured = 0
                names = []
                for e in t['Entities']:
                    if e['Extra'] == 'HEALTHY':
                        num_healthy += 1
                        names.append(e['Name'])
                    elif e['Extra'] == 'INJURED':
                        num_injured += 1
                        names.append(e['Name'])
                self.territories[t['Name']].reset(num_healthy, num_injured, names)
                self.territories[t['Name']].state = t['CivilState']
                self.territories[t['Name']].blue_revealed = t['Revealed']
                    
    def start_turn(self):
        self.turn_num += 1
        
        if DO_PRINT:
            print("")
            print("->TURN ", self.turn_num, "<-")

        self.broadcast_event("START_TURN", self.turn_num)

                     
    def end_turn(self):
        if self.turn_num%2 == 0 and not self.turn_num == 0:
            if DO_PRINT: 
                print("")
           
            if DO_CONSUMPTION_PHASE:
                self.consume_phase()
        if self.turn_num%3 == 0 and not self.turn_num == 0:
            if DO_PRINT:
                print("")
                print("* Strategic resupply *")    
            self.strat_resupply(Game.RESUPPLY_NUM)
        
        self.broadcast_event("END_TURN", self.turn_num)
        
        
    def consume_phase(self):
        for t in self.territories.values():
            t.consume()
        
        if "CONSUME" in self.listeners_dict.keys():
                for listener in self.listeners_dict["CONSUME"]:
                    listener.on_event("CONSUME")

             
    def strat_resupply(self, num_supplies):
        #additional supply cubes will be loaded into the SPOD FOB
        for t in self.territories.values():
            if t.has_pod(POD.SEA):
                supplies = list()
                for i in range(0, num_supplies):
                    supply = Supply()
                    supplies.append(supply)

                if DO_PRINT:
                    print("FOB " + t.name + " now has " + str(num_supplies) + " additional supplies")   

                t.add_supplies(supplies)
        
        if "RESUPPLY" in self.listeners_dict.keys():
                for listener in self.listeners_dict["RESUPPLY"]:
                    listener.on_event("RESUPPLY")
            
            
    def broadcast_event(self, event_name, *args):
        if event_name in self.listeners_dict.keys():
                for listener in self.listeners_dict[event_name]:
                    listener.on_event(event_name, *args)
            
                
    def add_entity(self, entity, surface):
        if entity.name in self.entities_on_board.keys():
            self.move_entity(entity, entity.surface, surface)
        else:
            self.entities[entity.name] = entity
            self.entities_on_board[entity.name] = entity
            entity.territory = surface.territory
            entity.surface = surface
            
            x, y = surface.get_placement_position()
            surface.add_token(entity, x, y)
            
            if "ADD_ENTITY" in self.listeners_dict.keys():
                for listener in self.listeners_dict["ADD_ENTITY"]:
                    listener.on_event("ADD_ENTITY", entity)

                                     
    def remove_entity(self, entity):
        if entity.name in self.entities_on_board:
            territory = entity.territory
            if entity.surface != None:
                entity.surface.remove_token(entity)
                entity.territory = None
                
            del self.entities_on_board[entity.name]
            
            if "REMOVE_ENTITY" in self.listeners_dict.keys():
                for listener in self.listeners_dict["REMOVE_ENTITY"]:
                    listener.on_event("REMOVE_ENTITY", entity, territory)
     
    def move_entity(self, entity, prev_surface, new_surface):
        if entity.name in self.entities_on_board:
            prev_surface.remove_token(entity)
           
            entity.territory = new_surface.territory
            entity.surface = new_surface
            
            x, y = new_surface.get_placement_position()
            new_surface.add_token(entity, x, y)
            
            if "ENTITY_MOVED" in self.listeners_dict.keys():
                for listener in self.listeners_dict["ENTITY_MOVED"]:
                    listener.on_event("ENTITY_MOVED", entity)
        else:
            self.add_entity(entity, new_surface)
                
    def evacuate_civilian(self, civilian):
        if isinstance(civilian, Civilian):
            self.remove_entity(civilian)
            self.rescues += 1
            
            if "CIVILIAN_RESCUED" in self.listeners_dict.keys():
                for listener in self.listeners_dict["CIVILIAN_RESCUED"]:
                    listener.on_event("CIVILIAN_RESCUED", civilian)
                
    def kill_civilian(self, civilian):
        if isinstance(civilian, Civilian):
            self.remove_entity(civilian)
            self.deaths += 1
            
            if "CIVILIAN_DIED" in self.listeners_dict.keys():
                for listener in self.listeners_dict["CIVILIAN_DIED"]:
                    listener.on_event("CIVILIAN_DIED", civilian)
            
    def add_listener(self, listener, event_name):
    #PERFORMANCE IMPROVEMENT
    #Using the listener dictionary to create list of listeners for each event type to ensure only the necessary event handlers are called
        if event_name in self.listeners_dict.keys():
            if not listener in self.listeners_dict[event_name]:
                self.listeners_dict[event_name].append(listener)
        else:
            self.listeners_dict[event_name] = [listener]
            
    def remove_listener(self, listener, event_name):
        if event_name in self.listeners_dict.keys():
            if listener in self.listeners_dict[event_name]:
                self.listeners_dict[event_name].remove(listener)

                  
    def on_click(self, x, y):
        handled = False
        for t in self.territories.values():
            handled = handled or t.on_click(x,y)
        return handled

    def get_score(self):
        return self.rescues * 2 - self.deaths
                
#==============================================================================                
    
class Population:
    NORMAL = "NORMAL"
    HUNGRY = "HUNGRY"
    UNREST = "UNREST"
    
    NONE = "NONE"
    CITY = "CITY"
    TOWN = "TOWN"
    VILLAGE = "VILLAGE"

#==============================================================================

class Territory:
    def __init__(self, name = "", surfaces = []):
        self.name = name
        self.size = Population.NONE
        self.state = Population.NORMAL
        
        self.game = None
        self.blue_revealed = False
        self.red_revealed = False
        
        self.lands = []
        self.seas = []
        self.airs = []
        
        self.civilians = {}
        self.supplies = []
        self.pods = []
        
        for surface in surfaces:
            if surface.mobility_type == Surface.LAND:
                surface.territory = self
                self.lands.append(surface)
            elif surface.mobility_type == Surface.AIR:
                surface.territory = self
                self.airs.append(surface)
            elif surface.mobility_type == Surface.WATER:
                surface.territory = self
                self.seas.append(surface)
            
                
    def reveal(self, entity):
        if entity.side == Side.BLUE and not self.blue_revealed:
            self.blue_revealed = True
            self.game.broadcast_event("TERRITORY_REVEAL", self, entity)
        elif entity.side == Side.RED and not self.red_revealed:
            self.red_revealed = True
            self.game.broadcast_event("TERRITORY_REVEAL", self, entity)
                
    #--------------------------------------------------------------------------           
    def reset(self, num_population=0, num_injured=0, names=[]):
        #clear all tokens
        self.supplies.clear()
        
        for land in self.lands:
            land.tokens.clear()
          
        for sea in self.seas:
            sea.tokens.clear()

        for air in self.airs:
            air.tokens.clear()
            
        self.blue_revealed = False
        self.red_revealed = False
        
        self.state = Population.NORMAL
        
        #if provided with values, seed the population
        if names != []:
            self.civilians.clear()
            self.create_population(self.size, num_population, num_injured, names)
        elif len(self.civilians.values()) == 0: 
            self.create_population(self.size)
        else:
            self._reset_civilians()              
        
        
    #--------------------------------------------------------------------------
    def get_all_surfaces(self):
        return self.lands + self.airs + self.seas
               
    
                                      
    # ---------------------------- supply methods ----------------------------- 
    def add_supplies(self, supplies):
        if isinstance(supplies, list):
            self.supplies.extend(supplies)
            self.game.broadcast_event("SUPPLIES_CHANGED", self) 
        elif isinstance(supplies, Supply):
            self.supplies.append(supplies)
            self.game.broadcast_event("SUPPLIES_CHANGED", self) 
        else:
            raise TypeError("not a list of Supply objects or Supply object")
                  
    def remove_supplies(self, num):
        max_num = num
        if max_num > len(self.supplies):
            max_num = len(self.supplies)
            
        supplies = list()
        for i in range(0, max_num):
            supply = self.supplies.pop(0)
            supply.territory = None
            supplies.append(supply)
        self.game.broadcast_event("SUPPLIES_CHANGED", self)    
        return supplies
    
    def remove_supply(self, supply):
        self.supplies.remove(supply)
        supply.territory = None
        self.game.broadcast_event("SUPPLIES_CHANGED", self)
    
    def num_supplies(self):
        return len(self.supplies)
    
    # -------------------------------------------------------------------------                
    def get_mobile_liftables(self):
        liftables = list()
        for land in self.lands:
            liftables.extend(land.get_mobile_liftables())
        return liftables
            
    #--------------------------------------------------------------------------
    def add_pod(self, pod):
        self.pods.append(pod)
        
    def remove_pod(self, pod):
        self.pods.remove(pod)

    def has_pod(self, podtype=None):
        if podtype is None:
            return len(self.pods) > 0
        for pod in self.pods:
            if pod.type == podtype:
                return True
            
    #--------------------------------------------------------------------------
    def _create_civilians(self, num_population, num_injured, names=[]):
        if names == []:
            for i in range(0, num_population):
                c = Civilian(Civilian.HEALTHY)
                self.civilians[c.name] = c
                self.add_civilian(c)
            for i in range(0, num_injured):
                c = Civilian(Civilian.INJURED)
                self.civilians[c.name] = c
                self.add_civilian(c)
        else:
            #create the population with particular names for seed
            if (len(names) == (num_population + num_injured)):
                nameID = 0
                for i in range(0, num_population):
                    c = Civilian(Civilian.HEALTHY, names[nameID])
                    nameID += 1
                    self.civilians[c.name] = c
                    self.add_civilian(c)
                for i in range(0, num_injured):
                    c = Civilian(Civilian.INJURED, names[nameID])
                    nameID += 1
                    self.civilians[c.name] = c
                    self.add_civilian(c)


    def create_population(self, size=Population.VILLAGE, num_population=0, num_injured=0, names=[]):
        if size != Population.NONE:
            #if provided with values, seed the population
            if names != []:
                self._create_civilians(num_population, num_injured, names)

            elif size == Population.CITY:
                if self.game.use_population_distribution:
                    num_population = random.randint(MIN_CIV_CITY, MAX_CIV_CITY)
                    num_injured = random.randint(MIN_INJURED, MAX_INJURED)
                else:
                    num_population = self.game.civ_city
                    num_injured = self.game.civ_injured

                self._create_civilians(num_population, num_injured)

            elif size == Population.TOWN:
                if self.game.use_population_distribution:
                    num_population = random.randint(MIN_CIV_TOWN, MAX_CIV_TOWN)
                    num_injured = random.randint(MIN_INJURED, MAX_INJURED)
                else:
                    num_population = self.game.civ_town
                    num_injured = self.game.civ_injured

                self._create_civilians(num_population, num_injured)

            elif size == Population.VILLAGE:
                if self.game.use_population_distribution:
                    num_population = random.randint(MIN_CIV_VILLAGE, MAX_CIV_VILLAGE)
                    num_injured = random.randint(MIN_INJURED, MAX_INJURED)
                else:
                    num_population = self.game.civ_village
                    num_injured = self.game.civ_injured

                self._create_civilians(num_population, num_injured)

            self.size = size
                  
    def _reset_civilians(self):
        for c in self.civilians.values():
            c.reset()
            self.add_civilian(c)
                
    #returns None if the population has not been revealed yet by either players
    def query_population(self, player):
        if player == Side.BLUE:
            if self.blue_revealed == True:
                return self.size, self.state, self.get_civilians()
        elif player == Side.RED:
            if self.blue_revealed or self.red_revealed:
                return self.size, self.state, self.get_civilians()
        return self.size, "Unknown", "Unknown"
    
    def add_civilian(self, civilian):
        if isinstance(civilian, Civilian):
            self.game.add_entity(civilian, self.lands[0])
                   
    def remove_civilian(self, civilian):
        if isinstance(civilian, Civilian):
            self.game.remove_entity(civilian)
       
   
    def remove_healthy_civilian(self):
        civilians = self.get_civilians()
        for c in civilians:
            if c.state == Civilian.HEALTHY:
                self.game.kill_civilian(c)
                return c
            
    def remove_injured_civilian(self):
        civilians = self.get_civilians()
        for c in civilians:
            if c.state == Civilian.INJURED:
                self.game.kill_civilian(c)
                return c
            
    def heal_civilian(self, num_to_heal):
        injured = [tok for tok in self.get_civilians() if tok.state == Civilian.INJURED]

        actual_healed = 0
        for c in injured:
            if num_to_heal > 0:
                c.state = Civilian.HEALTHY
                actual_healed += 1
                num_to_heal -= 1
            else:
                break
        if actual_healed != 0:
            self.game.broadcast_event("CIVILIANS_HEALED", self)
        return actual_healed
    
    def injure_civilian(self, num_to_injure):
        healthy = [tok for tok in self.get_civilians() if tok.state == Civilian.HEALTHY]

        actual_injured = 0
        for c in healthy:
            if num_to_injure > 0:
                c.state = Civilian.INJURED
                actual_injured += 1
                num_to_injure -= 1
            else:
                break
        if actual_injured != 0:
            self.game.broadcast_event("CIVILIANS_INJURED", self)
        return actual_injured        
            
    def get_civilians(self):
        civilians = [tok for tok in self.lands[0].tokens if isinstance(tok, Civilian)]
        #civilians.sort(key=lambda x: x.name) #Do we really need to ensure the same order of civilians
        return civilians

    def num_civilians(self):
        return len(self.get_civilians())

    def has_civilians(self):
        return self.num_civilians() > 0

    #--------------------------------------------------------------------------                               
    def on_click(self, x, y):
        land_handled = air_handled = sea_handled = False
        for l in self.lands:
            land_handled = land_handled or l.on_click(x, y)
        for a in self.airs:
            air_handled = air_handled or a.on_click(x, y)
        for s in self.seas:
            sea_handled = sea_handled or s.on_click(x, y)
        return land_handled or air_handled or sea_handled
    
    #--------------------------------------------------------------------------
    
    def set_position(self, x, y):
        for land in self.lands:
            land.x = x
            land.y = y
        for air in self.airs:
            air.x = x
            air.y = y
    
    def connect(self, territory):
        self.lands[0].connect(territory.lands[0])
        self.airs[0].connect(territory.airs[0])
        
    def get_land_connections(self):
        land_connections = list()
        for land in self.lands:
            land_connections.extend(land.connections)
        return land_connections
    
    def get_sea_connections(self):
        sea_connections = list()
        for sea in self.seas:
            sea_connections.extend(sea.connections)
        return sea_connections
    
    def get_air_connections(self):
        air_connections = list()
        for air in self.airs:
            air_connections.extend(air.connections)
        return air_connections
    
    #--------------------------------------------------------------------------
    def set_population_state(self, pop_state):
        if pop_state == Population.UNREST:
            if not self._has_any_infantry():
                self.state = pop_state
                if DO_PRINT: print("Unrest in " + self.name)
                return True
            else:
                return False
        else:
            self.state = pop_state
            return True
    
    
    def _has_any_infantry(self):
        tokens = list()
        for land in self.lands:
            tokens.extend([tok for tok in land.tokens if isinstance(tok, Inf)])
        if len(tokens) != 0:
            return True
        return False
            
    #--------------------------------------------------------------------------
    
    def consume(self, num_civilians_unit = 3):
        #territories with apods and spods don't need to feed civilians
        if self.pods != []:
            return
        
        #print("------Consume phase------")
        #calculate how many cubes were consumed
        #Refugees consume the supplies: remove 1 cube for every 
        #3 healthy or injured civilians 
        num_civilians = self.num_civilians()
        num_supplies_req = int(num_civilians / num_civilians_unit)
        if num_civilians % num_civilians_unit != 0:
            num_supplies_req += 1
            
        if DO_PRINT: print(self.name + " needs " + str(num_supplies_req) + " supplies")
        if num_supplies_req > len(self.supplies):
            
            #If there is no Hunger token present, place one in the territory
            #If there is a Hunger token present, flip it to Unrest.
            if self.state == Population.NORMAL:
                self.set_population_state(Population.HUNGRY)
                if DO_PRINT: print("Hunger in " + self.name)
            elif self.state == Population.HUNGRY:
                self.set_population_state(Population.UNREST)
                if DO_PRINT: print("Unrest in " + self.name)
                
                
            self.remove_healthy_civilian()
            num_supplies_req = len(self.supplies)
         
        if DO_PRINT: print(self.name + " consumed " + str(num_supplies_req) + " supplies")
        self.remove_supplies(num_supplies_req)
         
        #Remove 1 injured refugee: they have died from their wounds/disease.
        self.remove_injured_civilian()                 

#==============================================================================

class Surface:
    LAND = "LAND"
    WATER = "WATER"
    AIR = "AIR"
    counter = 1
    
    MAX_CIRCLE_POSITIONS = 10
      
    def __init__(self, name, mobility, elevation=1, parent_territory = None):
        self.tokens = []
        
        self.connections = []
        self.x = 0
        self.y = 0
        self.mobility_type = mobility
        self.elevation = elevation
        self.territory = parent_territory
        self.radius = 10
        self.name = name
        
        #this determines where the tokens are going to be placed within a
        #circular grid
        self.next_position_angle = 0

        #PERFORMANCE IMPROVEMENT
        #Generating a lookup table for the math calcuated angles as there are only a fixed number of angles
        #No need to calcuate the angle everytime get_placement_position is called
        self.angles = []
        for a in range(self.MAX_CIRCLE_POSITIONS):
            self.next_position_angle += 1
            angle = float(self.next_position_angle)*float(360/self.MAX_CIRCLE_POSITIONS)
            if angle >= 360:
                angle = 0
                self.next_position_angle = 0
            angle = math.radians(angle)
            self.angles.append((40*math.cos(angle),40*math.sin(angle)))
        
    def copy(self):
        copied_tokens = []
        for t in self.tokens:
            copied_t = t.copy()
            copied_tokens.append(copied_t)
        
        surface_copy = Surface(self.name, self.mobility, self.elevation, self.territory)
        surface_copy.tokens = copied_tokens
        surface_copy.x = self.x
        surface_copy.y = self.y
        return surface_copy
            
        
    def territory(self):
        return self.territory
        
    def on_click(self, x, y):
        if (pow(self.x - x, 2) + pow(self.y - y, 2)) <= pow(self.radius, 2):
            self.print_string()
            return True
        else:
            return False
          
    def connect(self, to_surface):
        if self.mobility_type == to_surface.mobility_type and self != to_surface:
            if not to_surface in self.connections:
                self.connections.append(to_surface)  
            if not self in to_surface.connections:
                to_surface.connections.append(self)
            return True
        return False
    
    def get_placement_position(self):
    #PERFORMANCE IMPROVEMENT
    #Using lookup table for math angles to reduce the number of calls to math functions
    #Lookup table initialised in __init__()
        if self.next_position_angle > (self.MAX_CIRCLE_POSITIONS - 1):
            self.next_position_angle = 0
        ret = self.angles[self.next_position_angle]
        x = self.x + ret[0]
        y = self.y + ret[1]
        self.next_position_angle += 1
        return x,y
    
    def add_token(self, token, x = None, y = None):
        if not (token in self.tokens):
            self.tokens.append(token)
            
            if x == None or y == None:
                token.x = self.x
                token.y = self.y
            else:
                token.x = x
                token.y = y
            
    def remove_token(self, token):
        if token in self.tokens:
            self.tokens.remove(token)
                     
    def get_mobile_liftables(self):
        liftables = [tok for tok in self.tokens if isinstance(tok, MobileEntity) and tok.can_be_lifted and not tok.lifted]
        return liftables
    
    def has_infantry(self):
        infantry_toks = [tok for tok in self.tokens if isinstance(tok, Inf)]
        return len(infantry_toks) != 0
    
    def _print_territory_info(self, territory):
        print("Territory name:" + territory.name + "," + self.mobility_type + "," + " elevation:" + str(self.elevation))
        print("Connections to territories:")
        for c in self.connections:
            if c.territory == None:
                for t1 in c.territories:
                    if t1 != territory:
                        print(t1.name)
            else:
                if c.territory != territory:
                    print(c.territory.name)
        
        
        print("Tokens:" + str([tok.name for tok in self.tokens]))
        print("In territory:" + str(len(territory.get_civilians())) + " civilians " 
              + str(len(territory.supplies)) + " supplies " +  str(len(territory.pods)) + " pods ")
        
        size, status, citizens = territory.query_population(Side.BLUE)
        if status == "Unknown":
            print("Blue query civilian:" + size + "," + status + "," + citizens) 
        else:
            print("Blue query civilian:" + size + "," + status + "," + str([c.name + "/" + c.state for c in citizens])) 
                  
    def print_string(self):
        self._print_territory_info(self.territory)

#==============================================================================            
       
class Token:
    def __init__(self):
        self.territory = None
        self.name = ""
        self.x = 0
        self.y = 0
        
        
    def print_string(self):
        print(self.name)
        print("x:" + str(self.x) + ", y:" + str(self.y))
        
    def on_click(self, x, y):
        return

#==============================================================================

class Supply(Token):
    def __init__(self):
        super().__init__()
        self.name = "SUPPLY"
    
#==============================================================================  
    
class POD(Token):
    SEA = "SEA_POD"
    AIR = "AIR_POD"
    
    def __init__(self, pod_type=AIR):
        super().__init__()
        self.name = "POD"
        self.type = pod_type
        
    def print_string(self):
        print(self.name +  " " + self.type)
        print("x:" + str(self.x) + ", y:" + str(self.y))

#==============================================================================

class Side:
    BLUE = "BLUE"
    RED = "RED"
    NONE = "NONE"
    
class Phase:
    DAWN = "DAWN"
    DAY = "DAY"
    DUSK = "DUSK"
    NIGHT = "NIGHT"


#==============================================================================
    
class Entity(Token):
    counter = 1
    def __init__(self):
        super().__init__()
        
        #entity run time variables
        self.turn_ended = False
        self.lifted = False
        self.alive = True
        self.surface = None
        
        #entity properties
        self.side = Side.NONE
        self.can_be_lifted = False
        self.id = Entity.counter
        self.graphics = None
        self.player = None
        Entity.counter += 1
        
    def set_side(self, side):
        self.side = side
        
    def reset(self):
        self.turn_ended = False
        self.lifted = False
        self.alive = True
        self.remove()
        
    def draw(self, surface):
        if self.graphics != None:
            self.graphics.draw(surface)
         
    #lifts and places the entity on the next surface
    def place(self, next_surface):
        #if we have no assigned territory, it means we haven't been placed
        #on the game board yet.
        if self.territory == None:
            next_surface.territory.game.add_entity(self, next_surface)
        else:
            self.territory.game.move_entity(self, self.surface, next_surface)
            
    #removes the entity from the current surface that it is on
    def remove(self):
        if self.territory != None:
            self.territory.game.remove_entity(self)
            self.territory = None
    
    def start_turn(self):
        self.turn_ended = False
    
    def end_turn(self):
        self.turn_ended = True

    def do_pass(self):
        return True

    def on_enter_phase(self, phase):
        pass
    
    def on_exit_phase(self, phase):
        pass
#==============================================================================        

class MobileEntity(Entity):
    def __init__(self):
        super().__init__()
        self.max_movement_points = 0
        self.movement_points = 0
        self.move_land = False
        self.move_water = False
        self.move_air = False
        self.player = None
        
        
#TODO: resurrect animation code
#        if USE_PYGAME: 
#            from engine import MobileEntityLerp
#            self.lerp = MobileEntityLerp(self)
        
               
    #reports on the current territory that this entity is on
    def isr(self):
        if self.territory != None:
            if self.side == Side.BLUE and self.territory.blue_revealed == False:
                self.territory.reveal(self)
                if DO_PRINT: print(self.name + " performed ISR on " + str(self.territory.name))
            elif self.side == Side.RED and self.territory.red_revealed == False:
                self.territory.reveal(self)
                if DO_PRINT: print(self.name + " performed ISR on " + str(self.territory.name))
     
          
    #moves to the next surface. MobileEntities should use this method to move around
    def move(self, next_surface):
        if not self.turn_ended and not self.lifted:
            #check to see if the entity has enough movement points
            #to move to the new surface based on its elevation 
            if next_surface.mobility_type == Surface.LAND:
                if self.movement_points - next_surface.elevation >= 0:
                    if DO_PRINT:
                        print(self.name, "moved:", self.surface.territory.name, "to", next_surface.territory.name)
                    self.place(next_surface)
                    self.movement_points -= next_surface.elevation
                    return True
                else:
                    if DO_PRINT: 
                        print(self.name + "has no more movement points")
                    #do isr as soon as we run out of movement points
                    print("land entity", self.name, "performing isr")
                    self.isr()
                    return False
            else:
                if self.movement_points > 0:
                    if DO_PRINT:
                        print(self.name, "moved:", self.surface.territory.name, "to", next_surface.territory.name)
                    super().place(next_surface)
                    self.movement_points -= 1
                    return True
                else:
                    if DO_PRINT: 
                        print(self.name + "has no more movement points.")
                    #do isr as soon as we run out of movement points
                    self.isr()
                    return False
        return False
    
    
    def get_valid_moves(self):
        land_connections = []
        sea_connections = []
        air_connections = []
        
        if not self.turn_ended and not self.lifted:
            if self.move_land and self.surface:
                land_connections = [c for c in self.surface.connections if c.mobility_type == Surface.LAND and (self.movement_points - c.elevation) >= 0]
            if self.move_water and self.surface:
                sea_connections =  [c for c in self.surface.connections if c.mobility_type == Surface.WATER and self.movement_points > 0]
            if self.move_air and self.surface:
                air_connections = [c for c in self.surface.connections if c.mobility_type == Surface.AIR and self.movement_points > 0]
        
        return land_connections, sea_connections, air_connections
    
    def start_turn(self):
        super().start_turn()
        self.movement_points = self.max_movement_points

    def do_pass(self):
        self.movement_points = 0
        self.isr()
        return True
    
#    def end_turn(self):
#        if not self.turn_ended:
#            super().end_turn()
#            self.isr()
            
    def on_exit_phase(self, phase):
        if phase == Phase.DAY:
            self.isr()
        super().on_exit_phase(phase)
        
#==============================================================================
        
class Civilian(Entity):
    HEALTHY = "HEALTHY"
    INJURED = "INJURED"
    
    counter = 1
    def __init__(self, state=HEALTHY, givenName=None):
        super().__init__()
        self.state = state
        self.initial_state = state
        if givenName != None:
            self.name = givenName
        else:
            self.name = "CIVILIAN_" + str(Civilian.counter)
        self.can_be_lifted = True
        Civilian.counter += 1
        
    def reset(self):
        super().reset()
        self.state = self.initial_state
            
    def print_string(self):
        print(self.name + ", state:" + self.state)
        
    #lifts and places the entity on the next surface
    def place(self, next_surface):
        next_surface.territory.add_civilian(self)
            
    #removes the entity from the current surface that it is on
    def remove(self):
        if self.territory != None:
            self.territory.remove_civilian(self)

#==============================================================================
    
class LiftEntity(MobileEntity):
    SUPPLY = "SUPPLY"
    PAX = "PAX"
    
    def __init__(self):
        super().__init__()
        self.cargo = list()
        self.supply_capacity = 0
        self.pax_capacity = 0
        self.carry_mode = LiftEntity.SUPPLY
        
    def reset(self):
        super().reset()
        self.cargo.clear()  
        self.carry_mode = LiftEntity.SUPPLY
        
    def set_carry_mode(self, mode):
        if self.is_empty() and (mode == LiftEntity.SUPPLY or mode == LiftEntity.PAX):
            self.carry_mode = mode
            return True
        return False
    
    def current_load(self):
        return len(self.cargo)
        
    def is_empty(self):
        return len(self.cargo) == 0
    
    def is_full(self):
        current_load = self.current_load()
        if current_load != 0:
            if self.carry_mode == LiftEntity.SUPPLY:
                return current_load >= self.supply_capacity
            elif self.carry_mode == LiftEntity.PAX:
                return current_load >= self.pax_capacity
        return False
          
    def _lift(self, cargo):
        if isinstance(cargo, list):
            self.cargo.extend(cargo)
        else:
            self.cargo.append(cargo)
                    
    def lift_supply(self, num):
        if not self.turn_ended and not self.lifted:
            max_num = num
            if max_num < 0:
                return False
            
            #can't carry both supplies and passenges
            current_supply_capacity = len(self.cargo)
            if current_supply_capacity != 0 and self.carry_mode == LiftEntity.PAX:
                return False
            
            territory = self.territory
            #can't carry more than the number of supplies in the current
            #territory
            if max_num > territory.num_supplies():
                max_num = territory.num_supplies()
                
            #can't carry more than the supply capacity
            if max_num > self.supply_capacity - current_supply_capacity:
                max_num = self.supply_capacity - current_supply_capacity
            if max_num <= 0:
                return False
            
            if DO_PRINT: print(self.name + " is lifting " + str(max_num) + " supplies from " + territory.name)
            supplies = territory.remove_supplies(max_num)
            self.set_carry_mode(LiftEntity.SUPPLY)
            self._lift(supplies)
            return True
        
        return False
        
    def drop_supply(self, num):
        if not self.turn_ended and not self.lifted:
            max_num = num
            if max_num <= 0:
                return False
            
            current_supply_capacity = len(self.cargo)
            if current_supply_capacity != 0:
                if max_num > current_supply_capacity:
                    max_num = current_supply_capacity
                    
                for i in range(0, max_num):
                    self.territory.add_supplies(self.cargo.pop(0))
                if DO_PRINT: print(self.name + " is dropping " + str(max_num) + " supplies to " + self.territory.name)
                return True    
                    
        return False
                    
    def lift_pax(self, pax):
        #TODO: pax.territory=NONE! when it should have a territory
        if not self.turn_ended and not self.lifted:
            in_territory = False
            
            if self.territory == pax.territory:
                in_territory = True
            else:
                if DO_PRINT: print("LiftEntity ", self.name, "not in proximity of", pax.name)
             
            if in_territory:
                #can't carry both supplies and passengers
                if len(self.cargo) != 0 and self.carry_mode == LiftEntity.SUPPLY:
                    return False
                
                if len(self.cargo) < self.pax_capacity:
                    #only if the passenger is currently not being lifted by another 
                    #vehicle
                    if pax.can_be_lifted and not pax.lifted:
                        #cannot lift civilians in territories that are in the UNREST state
                        if isinstance(pax, Civilian):
                            if pax.territory.state == Population.UNREST:
                                if DO_PRINT: print(self.name + " cannot lift " + pax.name + " from unrest territory: " + pax.territory.name)
                                return False
                        
                        if DO_PRINT: 
                            print(self.name + " is lifting " + pax.name + " from " + pax.territory.name)
                        pax.lifted = True
                        pax.remove()
                        
                        self.set_carry_mode(LiftEntity.PAX)
                        self._lift(pax)
                        return True
        return False
                
    def drop_pax(self, pax):
        #TODO: check that pax!=NONE
        if not self.turn_ended and not self.lifted:
            if pax in self.cargo:
                self.cargo.remove(pax)
                pax.lifted = False
                pax.turn_ended = True
                self.territory.game.add_entity(pax, self.territory.lands[0])
                if DO_PRINT: 
                    print(self.name + " is dropping " + pax.name + " to " + pax.territory.name)

                return True
        return False
     
    def get_liftable_civilians(self):
        if not self.turn_ended and not self.lifted:
            liftable_civilians = []
            if self.territory != None:
                liftable_civilians.extend(self.territory.get_civilians())
            
            return liftable_civilians
        return []
            
    def get_liftable_mobile_entities(self):
        if not self.turn_ended and not self.lifted:
            retlist = []
            if self.territory != None:
                retlist = [entity for entity in self.territory.get_mobile_liftables() if entity != self]
            else:
                liftables = []
                for t in self.surface.territories:
                    liftables.extend(t.get_mobile_liftables())
                retlist = [entity for entity in liftables if entity != self]
            
            #if len(retlist) != 0:
            return retlist
        return []
                  
    #def move(self, next_surface):
    #    moved = super().move(next_surface)
        #for c in self.cargo:
        #    c.x = self.x
        #    c.y = self.y
        #    c.territory = self.territory
    #    return moved
        
    def end_turn(self):
        super().end_turn()

#==============================================================================
        
class OPV(LiftEntity):
    counter = 1
    def __init__(self, givenName=None):
        super().__init__()
        if givenName != None:
            self.name = givenName
        else:
            self.name = "OPV_" + str(OPV.counter)
        self.move_water = True
        self.supply_capacity = 3
        self.pax_capacity = 3
        self.side = Side.BLUE
        self.img_file = './images/opv.png'
        #self.img_file = './images/opv_small.png'
        self.interdictedBoat = False
        
        if DEBUG_MOVEMENT:
            self.max_movement_points = 1000000000
        else:
            self.max_movement_points = 3
            
        self.movement_points = self.max_movement_points
        OPV.counter += 1
            
        
    def interdict(self):
        self.interdictedBoat = False
        civilians = [c for c in self.cargo if isinstance(c, Civilian)]
        #can only interdict if not carrying civilians
        if len(civilians) == 0:
           #check for any fishing boats and interdict them
            fishingboats = [tok for tok in self.surface.tokens if isinstance(tok, FishingBoat)]
            if len(fishingboats) != 0:
                for fb in fishingboats:
                    fb.remove()
                    fb.alive = False
                    if DO_PRINT: print(self.name + " interdicted fishing boat " + fb.name)
                    
                    if fb.militia != None:
                        if DO_PRINT: print(self.name + " found militia " + fb.militia.name) 
                    print(self.name + " cannot unload during the following Dusk phase")
                self.interdictedBoat = True
                return True
            return False
        return False
        
    def end_turn(self):
        super().end_turn()
        
    def get_liftable_civilians(self):
        #can't lift injured civilians
        civilians = [c for c in super().get_liftable_civilians() if c.state != Civilian.INJURED]
        return civilians

    def get_liftable_mobile_entities(self):
        liftable_mobile_entities = [m for m in super().get_liftable_mobile_entities() if not isinstance(m, MotCoy)]
        return liftable_mobile_entities
    
    def on_enter_phase(self, phase):
        if phase == Phase.DUSK:
            self.interdict()
        super().on_enter_phase(phase)
            

#==============================================================================       
          
class MotCoy(LiftEntity):
    counter = 1
    def __init__(self, givenName=None):
        super().__init__()
        if givenName != None:
            self.name = givenName
        else:
            self.name = "MOTCOY_" + str(MotCoy.counter)
        MotCoy.counter += 1
        self.move_land = True
        self.supply_capacity = 2
        self.pax_capacity = 2
        self.can_be_lifted = True
        self.side = Side.BLUE
        self.img_file = './images/motcoy.png'
        #self.img_file = './images/motcoy_small.png'
        
        if DEBUG_MOVEMENT:
            self.max_movement_points = 1000000000
        else:
            self.max_movement_points = 6
        
        self.movement_points = self.max_movement_points
        
    def lift_pax(self, pax):
        if isinstance(pax, MotCoy):
            return False
        return super().lift_pax(pax)
    
    def get_liftable_civilians(self):
        #can't lift injured civilians
        civilians = [c for c in super().get_liftable_civilians() if c.state != Civilian.INJURED]
        return civilians
    
    def get_liftable_mobile_entities(self):
        liftable_mobile_entities = [m for m in super().get_liftable_mobile_entities() if not isinstance(m, MotCoy)]
        return liftable_mobile_entities
    
    def do_isr(self):
        if self.movement_points > 0:
            self.isr()
            self.movement_points -= 1
            return True
        print(self.name + " does not have enough movement points to conduct ISR on " + self.territory.name)
        return False
        
#==============================================================================               

class MRH(LiftEntity):
    counter = 1
    MAX_FUEL = 2
    def __init__(self, givenName=None):
        super().__init__()
        if givenName != None:
            self.name = givenName
        else:
            self.name = "MRH_" + str(MRH.counter)
        self.move_air = True
        self.pax_capacity = 3
        self.supply_capacity = 0
        self.fuel = 0
        self.side = Side.BLUE
        self.img_file = './images/MRH-90.png'
        #self.img_file = './images/MRH-90_small.png'
        self.reachT9 = []
        self.reachT15 = []
        self.previousFOB = None
        
        if DEBUG_MOVEMENT:
            self.max_movement_points = 1000000000
        else:
            self.max_movement_points = 3
            
        self.movement_points = self.max_movement_points        
        MRH.counter += 1


    def reachableFOB(self):
        t9 = self.player.engine.game.territories['T9']
        t15 = self.player.engine.game.territories['T15']

        if not self.reachT9:
            for c in t9.airs[0].connections:
                self.reachT9.append(c)
        if not self.reachT15:
            for c in t15.airs[0].connections:
                self.reachT15.append(c)

        for c in range(self.movement_points - 1):
            newConnections = []
            for t in self.reachT9:
                for c in t.connections:
                    if (c not in self.reachT9) & (c not in newConnections) & (c.territory.name != 'T9'):
                        newConnections.append(c)
            for c in newConnections:
                self.reachT9.append(c)
            newConnections.clear()

            for t in self.reachT15:
                for c in t.connections:
                    if (c not in self.reachT15) & (c not in newConnections) & (c.territory.name != 'T15'):
                        newConnections.append(c)
            for c in newConnections:
                self.reachT15.append(c)
            newConnections.clear()
            
    def _is_lifting_injured(self):
        if self.is_empty():
            return False
        for tok in self.cargo:
            if isinstance(tok, Civilian):
                if tok.state == Civilian.INJURED:
                    return True
        return False
    
    def _crash(self):
        if DO_PRINT:print(self.name + " has crashed!")
        
        #kill all the cargo that the MRH was carrying
        for tok in self.cargo:
            if DO_PRINT:print(tok.name + " has died!")
            if isinstance(tok, Civilian):
                self.territory.game.deaths += 1
        
        #kill the MRH        
        self.alive = False
        self.remove()
                
    
    def lift_pax(self, pax):
        if isinstance(pax, MotCoy):
            return False
        
        if self._is_lifting_injured():
            if isinstance(pax, Civilian):
                if pax.state == Civilian.INJURED:
                    return super().lift_pax(pax)
                else:
                    return False
            else:
                return False
            
        return super().lift_pax(pax)
    
    def get_liftable_mobile_entities(self):
        return [entity for entity in super().get_liftable_mobile_entities() 
                if not isinstance(entity, MotCoy)]
    
    def start_turn(self):
        super().start_turn()
        if self.territory != None and self.territory.has_pod(POD.AIR):
            self.fuel = MRH.MAX_FUEL
            self.previousFOB = self.territory
        
    
    def end_turn(self):
        if not self.turn_ended:
            super().end_turn()
             #destroy the helicopter if it has crashed
            self.fuel -= 1
            if self.fuel < 0:
                self._crash()
            else:
                if not self.territory.pods:
                    if DO_PRINT:
                        print(self.name, "has", self.fuel, "fuel left.")

    #overload: only give option to move back to reachable FOBs when MRH did not start turn in FOB
    def get_valid_moves(self):
        land_connections = []
        sea_connections = []
        air_connections = []
        
        if not self.turn_ended and not self.lifted:
            if self.move_air and self.surface:
                if self.fuel == 1:
                    if (self.surface.territory.name != 'T9') & (self.surface.territory.name != 'T15'):
                        if DO_PRINT:
                            print(self.name + " has limited fuel left and must return to a FOB")
                    if (self.surface in self.reachT9) & (self.surface.territory.name != 'T15'):
                        air_connections.append(self.player.engine.game.territories['T9'].airs[0])
                    if (self.surface in self.reachT15) & (self.surface.territory.name != 'T9'):
                        air_connections.append(self.player.engine.game.territories['T15'].airs[0])
                else:
                    air_connections = [c for c in self.surface.connections if c.mobility_type == Surface.AIR and self.movement_points > 0]
        
        return land_connections, sea_connections, air_connections
       
        
#==============================================================================
                 
class Inf(MobileEntity):
    counter = 1
    def __init__(self, givenName=None):
        super().__init__()
        if givenName != None:
            self.name = givenName
        else:
            self.name = "INF_" + str(Inf.counter)
        self.move_land = True
        self.can_be_lifted = True
        self.side = Side.BLUE
        self.img_file = './images/inf.png'
        #self.img_file = './images/inf_small.png'
        
        if DEBUG_MOVEMENT:
            self.max_movement_points = 1000000000
        else:
            self.max_movement_points = 3
            
        self.movement_points = self.max_movement_points
        Inf.counter += 1
            
        
    def arrest(self):
        if not self.turn_ended and not self.lifted:
            
            if self.surface == None and DO_PRINT:
                print("Surface of " + self.name + " is None. Check to see if token is on game board.")
                
            #check for any militia unit and remove them from game
            militias = [tok for tok in self.surface.tokens if isinstance(tok, Militia)]
            for m in militias:
                m.remove()
                m.alive = False
                if DO_PRINT:print(self.name + " arrested " + m.name)
                self.end_turn()
            
    def police(self):
        if not self.turn_ended and not self.lifted:
            if self.territory != None:
                #remove any unrest token from the territory
                if self.territory.state == Population.UNREST:
                    self.territory.set_population_state(Population.NORMAL)
                    if DO_PRINT:print(self.name + " restored order to " + self.territory.name)
                    self.end_turn()
        
    def end_turn(self):
        super().end_turn()
        
     
    def on_enter_phase(self, phase):
        if phase == Phase.DUSK:
            self.police()
            self.arrest()
        super().on_enter_phase(phase)
        
#==============================================================================
class Medic(MobileEntity):
    MAX_NUM_HEALED = 2
    
    counter = 1
    def __init__(self, givenName=None):
        super().__init__()
        if givenName != None:
            self.name = givenName
        else:
            self.name = "MEDIC_" + str(Medic.counter)
        Medic.counter += 1
        self.move_land = True
        self.can_be_lifted = True
        self.side = Side.BLUE
        self.img_file = './images/medic.png'
        #self.img_file = './images/medic_small.png'
        
        if DEBUG_MOVEMENT:
            self.max_movement_points = 1000000000
        else:
            self.max_movement_points = 1
            
        self.movement_points = self.max_movement_points
        

    #heals a number of civilians (num_to_be_healed) in the current territory
    def heal(self, num_to_be_healed):
        if not self.turn_ended and not self.lifted:
            num_healed = self.territory.heal_civilian(num_to_be_healed)
            if num_healed != 0:
                if DO_PRINT: print("Medic", self.name, "healed", num_healed, "civilians")
                self.end_turn()
            return num_healed
        return 0
                
            
    def move(self, next_surface, animate=False):
        if not self.turn_ended and not self.lifted:
            if self.movement_points != 0:

                if DO_PRINT:
                    print(self.name + " moved: " + self.territory.name + " to " + next_surface.territory.name)
                if animate:
                    self.lerp.move(next_surface)
                else:
                    self.place(next_surface)
                self.movement_points -= 1
                return True
            else:
                return False
        return False
    
    def on_enter_phase(self, phase):
        if phase == Phase.DUSK:
            self.heal(Medic.MAX_NUM_HEALED)
        super().on_enter_phase(phase)

    #overload: move independently over land into any one adjacent territory on foot (regardless of elevation)
    def get_valid_moves(self):
        land_connections = []
        sea_connections = []
        air_connections = []
        
        if not self.turn_ended and not self.lifted:
            if self.move_land and self.surface:
                land_connections = [c for c in self.surface.connections if c.mobility_type == Surface.LAND and self.movement_points > 0]
                    
        return land_connections, sea_connections, air_connections
        
#==============================================================================
class FishingBoat(LiftEntity):
    counter = 1
    def __init__(self, militia = None, givenName=None):
        super().__init__()
        if givenName != None:
            self.name = givenName
        else:
            self.name = "FishBoat_" + str(FishingBoat.counter)
        FishingBoat.counter += 1
        self.move_water = True
        self.side = Side.RED
        self.militia = None
        self.deployed_militia = False
        self.img_file = './images/fish_boat.png'
        
        if DEBUG_MOVEMENT:
            self.max_movement_points = 100000000
        else:
            self.max_movement_points = 3
            
        self.movement_points = self.max_movement_points
          
        self.pax_capacity = 1
        self.supply_capacity = 0
        
        if militia != None and isinstance(militia, Militia):
            self.militia = militia

    def set_side(self, side):
        self.side = side
        if self.militia != None:
            self.militia.set_side(side)
                
    def reset(self):
        self.deployed_militia = False
        super().reset()
            
    def deploy_militia(self):
        if self.deployed_militia == False:
            if self.militia != None:
                territory = self.surface.territory
                self.player.engine.game.add_entity(self.militia, self.surface)
                self.militia.place(territory.lands[0])
                self.deployed_militia = True
                if DO_PRINT:print(self.name + " deployed militia at " + territory.name)
                return True
        return False
            
        
#==============================================================================
class Militia(MobileEntity):
    counter = 1
    def __init__(self, givenName=None):
        super().__init__()
        if givenName != None:
            self.name = givenName
        else:
            self.name = "Militia_" + str(Militia.counter)
        Militia.counter += 1
        self.move_land = True
        self.side = Side.RED
        self.img_file = './images/militia.png'
        
        if DEBUG_MOVEMENT:
            self.max_movement_points = 100000000
        else:
            self.max_movement_points = 3
            
        self.movement_points = self.max_movement_points
            
    def sabotage_supply(self):
        if not self.turn_ended and not self.lifted:
            if self.territory != None:
                supplies = self.territory.remove_supplies(self.territory.num_supplies())
                if len(supplies) != 0:
                    if DO_PRINT:print(self.name + " sabotaged " + str(len(supplies)) + " in territory " + self.territory.name)
                    self.end_turn()
                    return True
        return False
                
    def injure_population(self, num_to_be_injured):
        if not self.turn_ended and not self.lifted:
            if self.territory != None:
                actual_injured = self.territory.injure_civilian(num_to_be_injured)
                if actual_injured != 0:
                    if DO_PRINT:print(self.name + " injured " + str(actual_injured) + " civilians in territory " + self.territory.name)
                    self.end_turn()
                    return True
        return False
    
    def cause_unrest(self):
        if not self.turn_ended and not self.lifted:
            if self.territory != None:
                unrest = self.territory.set_population_state(Population.UNREST)
                if unrest:
                    if DO_PRINT:print(self.name + " caused unrest in territory " + self.territory.name)
                    self.end_turn()
                    return True
        return False
                    
    def get_valid_moves(self):
        #militias cannot move onto lands with infantry on it
        lands, seas, airs = super().get_valid_moves()
        valid_lands = [l for l in lands if not l.has_infantry()]
        return valid_lands, seas, airs
            
#==============================================================================
    
class P8(MobileEntity):
    counter = 1
    def __init__(self, givenName=None):
        super().__init__()
        if givenName != None:
            self.name = givenName
        else:
            self.name = "P8_" + str(P8.counter)
        P8.counter += 1
        self.move_air = True
        self.side = Side.BLUE
        self.img_file = './images/P8.png'
        #self.img_file = './images/P8_small.png'
        
        if DEBUG_MOVEMENT:
            self.max_movement_points = 100000000
        else:
            self.max_movement_points = 1
            
        self.movement_points = self.max_movement_points
            
    def get_valid_moves(self):
        air_connections = []
        
        if self.movement_points > 0:
            #the P8 can move to any territory on the map
            for t in self.territory.game.territories.values():
                if t != self.territory:
                    air_connections.extend(t.airs)
            
        return [], [], air_connections
    
    def identify(self, entity):
        if self.movement_points > 0:
            if isinstance(entity, FishingBoat):
                self.place(entity.territory.seas[0])
                if entity.militia != None:
                    print(entity.name + " is a Militia Boat")
                else:
                    print(entity.name + " is a Fishing Boat")
                self.movement_points -= 1
                return True
        return False
    
    def end_turn(self):
        super().end_turn()
        
#==============================================================================
      
class C130(Entity):
    
    MAX_CIVILIAN_CAPACITY = 8
    MAX_SUPPLY_CAPACITY = 5
    
    counter = 1
    def __init__(self, givenName=None):
        super().__init__()
        if givenName != None:
            self.name = givenName
        else:
            self.name = "C130_" + str(C130.counter)
        C130.counter += 1
        self.apod_territories = []
        self.side = Side.BLUE
        self.cargo = []
        self.src_territories = {}
        self.img_file = './images/C130.png'
        #self.img_file = './images/c130_small.png'

    def reset(self):
        super().reset()
        self.cargo.clear()

    def load_civilians(self):
        if len(self.cargo) != 0 and not isinstance(self.cargo[0], Civilian):
            print(self.name, " already carrying ", self.cargo)
            return False
        
        if len(self.cargo) >= C130.MAX_CIVILIAN_CAPACITY:
            print(self.name, " at max capacity")
            return False
        
        for apod in self.apod_territories:
            civilians = apod.get_civilians()
            for c in civilians:
                if len(self.cargo) < C130.MAX_CIVILIAN_CAPACITY:
                    self.cargo.append(c)
                    c.lifted = True
                    apod.remove_civilian(c)
                    
        if len(self.cargo) == 0:
            if DO_PRINT:
                print("No civilians in ", self.territory.name, "to load by ", self.name)
            return False
        if DO_PRINT: 
            print(self.name, "loaded civilians", len(self.cargo))
        return True
    
    def load_supplies(self, num_supplies = None):
        if len(self.cargo) != 0 and not isinstance(self.cargo[0], Supply):
            print(self.name, "load_supplies:already carrying", self.cargo)
            return False
        
        if len(self.cargo) >= C130.MAX_SUPPLY_CAPACITY:
            print("Can't lift more supplies. Full")
            return False
        
        #supplies are stored at the sea pod
        spods = [t for t in self.territory.game.territories.values() if t.has_pod(POD.SEA)] 
        
        num_loaded = 0
        #if no number is specified, load the maximum supplies the C130 can carry whilst checking there is sufficent
        if num_supplies == None:
            for spod in spods:
                if len(self.cargo) >= C130.MAX_SUPPLY_CAPACITY:
                    #stop putting supplies when at max capacity
                    break
                
                supplies = spod.supplies
                #load supplies until you run out of supplies or the C130 is at max capacity
                while len(supplies) > 0 and len(self.cargo) < C130.MAX_SUPPLY_CAPACITY:
                    self.cargo.append(supplies[0])
                    spod.remove_supply(supplies[0])
                    num_loaded += 1
        #if a number is specified, load that many supplies in the C130 whilst checking there is sufficent
        else:
            supplies = spods[0].supplies
            for n in range(num_supplies):
                if len(supplies) > 0 and len(self.cargo) < C130.MAX_SUPPLY_CAPACITY:
                    self.cargo.append(supplies[0])
                    spods[0].remove_supply(supplies[0])
            num_loaded = num_supplies
                    
        if len(self.cargo) == 0:
            #print("*load_supplies*", self.name, self.cargo)
            return False
        if DO_PRINT:
                print(self.name, "loaded " + str(num_loaded) +" supply(s)")
        return True
    
    def load_entity(self, entity):
        if len(self.cargo) != 0:
            if isinstance(self.cargo[0], Civilian) or isinstance(self.cargo[0], Supply):
                print(self.name, "load_entity:already carrying", self.cargo)
                return False
            
        in_apod = False
        for apod in self.apod_territories:
            if apod == entity.territory:
                in_apod = True
                #keep track of the opposite apod territory so we know where to 
                #send the entity to
                self.src_territories[entity.name] = entity.territory
                break

        if in_apod:
            self.cargo.append(entity)
            if DO_PRINT: 
                print(self.name, "loaded", entity.name, "from apod in territory", entity.territory.name)
            entity.lifted = True
            entity.remove()
            return True
        
        return False
    
    def evacuate_civilians(self):
        num_civilians = len(self.cargo)
        #print(num_civilians, "num_civilians")
        if num_civilians != 0 and isinstance(self.cargo[0], Civilian):
            for c in self.cargo:
                self.territory.game.evacuate_civilian(c)  
                #if DO_PRINT: 
                    #print(c.name,"evacuated")

            self.cargo.clear()
            if DO_PRINT: print(self.name, "evacuated", num_civilians, "civilians")
            return True
    
        if DO_PRINT: print("evacuate_civilians returning False", self.cargo)
        return False
    
    def airdrop_supplies(self, target_territory, num_supplies):
        num_loaded = len(self.cargo)
        if num_loaded != 0 and isinstance(self.cargo[0], Supply):
            if num_supplies > num_loaded:
                num_supplies = num_loaded
            
            for i in range(0, num_supplies):
                target_territory.add_supplies(self.cargo.pop(0))
                
            if DO_PRINT: 
                print(self.name, "dropped", str(num_supplies), "supplies on territory", target_territory.name)
            return True
        print("**airdrop_supplies**", self.name, self.cargo)
        return False
    
    def airlift_entities(self):
        if len(self.cargo) !=0:
            if isinstance(self.cargo[0], Civilian) or isinstance(self.cargo[0], Supply):
                return False
            for e in self.cargo:
                src_territory = self.src_territories.pop(e.name, None)
                if src_territory != None:
                    # the target territory is the opposite one from the source
                    #territory
                    if src_territory == self.apod_territories[0]:
                        target_territory = self.apod_territories[1]
                    elif src_territory == self.apod_territories[1]:
                        target_territory = self.apod_territories[0]
                
                    e.place(target_territory.lands[0])
                    e.turn_ended = True
                    e.lifted = False
                
                    if DO_PRINT: 
                        print(self.name, "doing air lift on " + e.name + " to " + target_territory.name)
            
            self.cargo.clear()
            return True
        return False

    def unload_cargo(self, entity_name):
        if len(self.cargo) !=0:
            entity = None
            if entity_name == 'SUPPLY':
                entity = self.cargo[0]
                self.territory.add_supplies(entity)
            else:
                entity = self.player.engine.game.entities[entity_name]
                if isinstance(entity, Civilian):
                    self.territory.add_civilian(entity)
                elif isinstance(entity, MobileEntity):
                    entity.place(self.surface)
            self.cargo.remove(entity)
            if DO_PRINT: 
                print(self.name, "unloading " + entity_name + " to " + self.territory.name)
            return True
        if DO_PRINT:
            print(self.name, "unable to unload " + entity_name)
        return False
    
    def get_liftable_mobile_entities(self):
        mobile_liftables = []
        for apod in self.apod_territories:
            mobile_liftables.extend(apod.get_mobile_liftables())
        return mobile_liftables
 
        