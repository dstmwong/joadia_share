# -*- coding: utf-8 -*-
"""
Created on Mon Oct 15 15:12:06 2018

@author: wongm
"""

from core.model import Side, MobileEntity, C130, Phase, POD, LiftEntity, MotCoy, \
MRH, Militia, FishingBoat, OPV, Inf, Medic, P8, Civilian, Supply, Game
import core.model 
import json

#==============================================================================
class Player:
    
    def __init__(self, name = "", side = Side.BLUE):
        self.engine = None
        self.side = side
        self.entities = []
        
        self.name = name
        self.entities_to_be_updated = []
        self.phase_done = False
        
        self.record = True #child classes set this flag to false to disable recording
        self.recordBroadcasts = False
        self.recorded_moves = []
    
    
    def reset(self, entityReset=True):
        #PERFORMANCE IMPROVEMENT
        #When adding class as a listener, need to specify what event that wish to listen for
        self.engine.game.add_listener(self, "TERRITORY_REVEAL")
        self.engine.game.add_listener(self, "CIVILIAN_RESCUED")
        if entityReset:
            for entity in self.entities:
                entity.reset()    
        self.recorded_moves.clear()
     
    
    def on_event(self, event_name, *args):
        #record the TERRITORY_REVEALED event because there is no other component
        #that records that event when units move on a territory
        if self.recordBroadcasts:
            if event_name == "TERRITORY_REVEAL":
                #print(self.name, "on_event", event_name, args)
                territory = args[0]
                entity = args[1]
                if entity.side == Side.BLUE:
                    self.record_move([entity.name, event_name, territory.name])
            elif event_name == "CIVILIAN_RESCUED":
                entity = args[0]
                self.record_move([entity.name, event_name])
#            elif event_name == "CIVILIAN_DIED":
#                entity = args[0]
#                self.record_move([entity.name, event_name])
            
        
    #this method gives the Player a list of entities that it has to play with
    def set_entities(self, entities):
        for ent in entities:
            ent.set_side(self.side)
            ent.player = self    
        self.entities = entities

    #this method clears previous entities and creates new ones based on the names given
    #used for loading replay from JSON
    def create_entities(self, entities, territory=None):
        self.entities.clear()
        newT = []
        newEntities = []
        for e in entities:
            if 'FishBoat' in e[0]:
                militia = None
                if e[1] != '':
                    militia = Militia(e[1])
                if militia:
                    newEntities.append(FishingBoat(militia, e[0]))
                else:
                    newEntities.append(FishingBoat(None, e[0]))
            elif 'Militia' in e[0]:
                newEntities.append(Militia(e[0]))
            elif 'C130' in e[0]:
                newEntities.append(C130(e[0]))
            elif 'P8' in e[0]:
                newEntities.append(P8(e[0]))
            elif 'MRH' in e[0]:
                newEntities.append(MRH(e[0]))
            elif 'MOTCOY' in e[0]:
                newEntities.append(MotCoy(e[0]))
            elif 'INF' in e[0]:
                newEntities.append(Inf(e[0]))
            elif 'MEDIC' in e[0]:
                newEntities.append(Medic(e[0]))
            elif 'OPV' in e[0]:
                newEntities.append(OPV(e[0]))
        
        if newEntities:
            self.set_entities(newEntities)
            if territory:
                newT = self.engine.game.territories[territory]
                for ent in newEntities:
                    if isinstance(ent, MobileEntity):
                        if ent.move_land:
                            ent.place(newT.lands[0])
                        elif ent.move_air:
                            ent.place(newT.airs[0])
                        elif ent.move_water:
                            #water entities can be placed in two possible water surfaces for some territories
                            #desired surface can be given in replay file
                            surfaceName = None
                            for e in entities:
                                if ent.name == e[0]:
                                    if e[1] != '':
                                        surfaceName = e[1]
                            
                            placed = False
                            if surfaceName:
                                for s in newT.seas:
                                    if surfaceName == s.name:
                                        ent.place(s)
                                        placed = True
                                        break                            
                            if not placed:
                                ent.place(newT.seas[0])
                        
                        if isinstance(ent, MRH):
                            ent.reachableFOB()
            
                    if isinstance(ent, C130):
                        ent.place(newT.airs[0])
                        ent.apod_territories.clear()
                
                        for t in self.engine.game.territories.values():
                            if t.has_pod(POD.AIR):
                                ent.apod_territories.append(t)
                        

    #this method tells the game where to put the tokens in play before turn 1 starts
    #overwrite to change the initial placements of the tokens
    def place_entities(self, territories):
        for t in self.entities:
            if isinstance(t, MobileEntity):
                if t.move_land:
                    t.place(territories["T15"].lands[0])
                elif t.move_air:
                    t.place(territories["T15"].airs[0])
                elif t.move_water:
                    t.place(territories["T15"].seas[0])
                
                if isinstance(t, MRH):
                    t.reachableFOB()
    
            if isinstance(t, C130):
                t.place(territories["T15"].airs[0])
                t.apod_territories.clear()
                
                for territory in territories.values():
                    if territory.has_pod(POD.AIR):
                        t.apod_territories.append(territory)

       
    def start_turn(self):
        for entity in self.entities:
            entity.start_turn()
        self.recorded_moves.append([[], [], [], []])

    
    def end_turn(self):
        for entity in self.entities:
            entity.end_turn()
        self.phase_done = False

            
    def _goto_phase(self, to_phase, from_phase):
        valid_entities = [ent for ent in self.entities if ent.name in self.engine.game.entities_on_board                  
                          and ent.turn_ended == False and ent.lifted == False and ent.alive == True]
        
        if to_phase == Phase.DAWN:
            for e in valid_entities:
                e.on_exit_phase(from_phase)
                e.on_enter_phase(to_phase)
            self.phase_done = False
        elif to_phase == Phase.DAY:
            for e in valid_entities:
                e.on_exit_phase(from_phase)
                e.on_enter_phase(to_phase)
            self.phase_done = False
        elif to_phase == Phase.DUSK:
            for e in valid_entities:
                e.on_exit_phase(from_phase)
                e.on_enter_phase(to_phase)
            self.phase_done = False
        elif to_phase == Phase.NIGHT:
            for e in valid_entities:
                e.on_exit_phase(from_phase)
                e.on_enter_phase(to_phase)
            self.phase_done = False
        
        
    def do_turn(self):
        entities_to_be_updated = [ent for ent in self.engine.game.entities_on_board.values() 
        if ent.side == self.side and ent.player == self
        and ent.turn_ended == False and ent.lifted == False and ent.alive == True]
        
        if self.side == Side.BLUE:
            if self.engine.game.phase == Phase.DAWN:
                if self.phase_done:
                    self._goto_phase(Phase.DAY)
                else:
                    self.phase_done = self.do_dawn_phase(entities_to_be_updated, self.engine.game.territories)
            elif self.engine.game.phase == Phase.DAY:
                if self.phase_done:
                    self._goto_phase(Phase.DUSK)
                else:
                    self.phase_done = self.do_day_phase(entities_to_be_updated, self.engine.game.territories)
            elif self.engine.game.phase == Phase.DUSK:
                if self.phase_done:
                    self._goto_phase(Phase.NIGHT)
                    return True
                else:
                    self.phase_done = self.do_dusk_phase(entities_to_be_updated, self.engine.game.territories)
                    
        elif self.side == Side.RED:
            if self.engine.game.phase == Phase.NIGHT:
                if self.phase_done:
                    self._goto_phase(Phase.DAWN)
                    return True
                else:
                    self.phase_done = self.do_night_phase(entities_to_be_updated, self.engine.game.territories)
            else:
                print("--- red phase ---", self.engine.game.phase)
                                  
        return False

    
    def do_phase(self):
        if not self.phase_done:
            entities_to_be_updated = [ent for ent in self.engine.game.entities_on_board.values() 
            if ent.side == self.side and ent.player == self
            and ent.turn_ended == False and ent.lifted == False and ent.alive == True]
            
            if self.engine.game.phase == Phase.DAWN:
                self.phase_done = self.do_dawn_phase(entities_to_be_updated, self.engine.game.territories)
            elif self.engine.game.phase == Phase.DAY:
                self.phase_done = self.do_day_phase(entities_to_be_updated, self.engine.game.territories)
            elif self.engine.game.phase == Phase.DUSK:
                self.phase_done = self.do_dusk_phase(entities_to_be_updated, self.engine.game.territories)
            elif self.engine.game.phase == Phase.NIGHT:
                self.phase_done = self.do_night_phase(entities_to_be_updated, self.engine.game.territories)
                                  
        return self.phase_done 


    def record_move(self, move):
        current_turn_moves = self.recorded_moves[-1]
        if self.engine.game.phase == Phase.DAWN:
            move_list = current_turn_moves[0]
        elif self.engine.game.phase == Phase.DAY:
            move_list = current_turn_moves[1]
        elif self.engine.game.phase == Phase.DUSK:
            move_list = current_turn_moves[2]
        elif self.engine.game.phase == Phase.NIGHT:
            move_list = current_turn_moves[3]
            
        #TODO verify that the move input is actually valid
        move_list.append(move)
               
        
    def execute_move(self, entity_name, move_label, extra=None):
        done = False
        entity = None
        
        if entity_name in self.engine.game.entities:
            entity = self.engine.game.entities[entity_name]
        else:
            #...or in the list of entities that belongs to this player
            for e in self.entities:
                if e.name == entity_name:
                    entity = e
        
        if entity != None:
            if move_label == "pass":
                done = entity.do_pass()

            elif move_label == "move":
                loc=self.engine.game.get_surface(extra)
                done = entity.move(loc)
            
            elif move_label == "lift PAX":
                lifted=self.engine.game.entities[extra]
                entity.set_carry_mode(LiftEntity.PAX)
                done = entity.lift_pax(lifted)
              
            elif move_label == "lift supply":
                entity.set_carry_mode(LiftEntity.SUPPLY)
                done = entity.lift_supply(int(extra))
              
            elif move_label == "load civ":
                done = entity.load_civilians()
              
            elif move_label == "load max supplies":
                done = entity.load_supplies()
                
            elif move_label == "load supplies":
                done = entity.load_supplies(int(extra))
              
            elif move_label == "load units":
                lifted=self.engine.game.entities[extra]
                done = entity.load_entity(lifted)                        
     
            elif move_label == "evacuate":
                done = entity.evacuate_civilians()
              
            elif move_label == "airdrop supplies":
                to_territory = self.engine.game.territories[extra]
                done = entity.airdrop_supplies(to_territory, 1)
              
            elif move_label == "drop supplies":
                supplies=int(extra)
                done = entity.drop_supply(supplies)
              
            elif move_label == "lift units":
                done = entity.airlift_entities()
              
            elif move_label == "identify":
                boat=self.engine.game.entities[extra]
                done = entity.identify(boat)
              
            elif move_label == "interdict":
                done = entity.interdict()         
    
            elif move_label == "do isr":
                done = entity.do_isr()

            elif move_label == "drop PAX":
                done = False
                for cargo in entity.cargo:
                    if cargo.name == extra:
                        done = entity.drop_pax(cargo)
            
            elif move_label == "unload cargo":
                done = entity.unload_cargo(extra)

            elif move_label == "injure population":
                done = entity.injure_population(extra)
            
            elif move_label == "cause unrest":
                done = entity.cause_unrest()
            
            elif move_label == "sabotage supply":
                done = entity.sabotage_supply()
                
            elif move_label == "deploy militia":
                done = entity.deploy_militia()
             
            elif move_label == "launch boat":
                done = False
                territory = self.engine.game.territories[extra]
                if territory != None:
                    entity.place(territory.seas[0])
                    done = True

            else:
                print("unknown move", move_label)
        else:
            print("unknown entity:", entity_name)
            
        if done:
            if self.record:
                self.record_move([entity_name, move_label, extra])
        else:
            pass
            #print("problem with move:", move)
                 
        return done

    #--------------------------------------------------------------------------
    #below methods to be overloaded by child classes
    def do_dawn_phase(self, entities, territories):
        return True
    
    def do_day_phase(self, entities, territories):
        return True
    
    def do_dusk_phase(self, entities, territories):
        return True
    
    def do_night_phase(self, entities, territories):
        return True
    
    
    

#==============================================================================

class HumanPlayer(Player):
    def __init__(self, name = ""):
        super().__init__(name)
        self.controller = None

    def reset(self, entityReset=True):
        super().reset(entityReset)
    
    def do_dawn_phase(self, entities, territories):
        return True
        #return self.controller.handle_inputs(entities, events, Phase.DAWN)
        
    def do_day_phase(self, entities, territories):
        return True
        #return self.controller.handle_inputs(entities, events, Phase.DAY)
    
    def do_dusk_phase(self, entities, territories):
        return True
        #return self.controller.handle_inputs(entities, events, Phase.DUSK)
    
    def do_night_phase(self, entities, territories):
        return True
        #return self.controller.handle_inputs(entities, events, Phase.NIGHT)
        

#==============================================================================
import time

class TimerPlayer(Player):
    def __init__(self, name = ""):
        super().__init__(name)
        self.started = False
        self.start_ticks = -1
           
    def do_dawn_phase(self, entities, territories):
        if self.start_ticks == -1:
            self.start_ticks = time.clock()
            print(self.name + " started dawn phase")
        else:
            if (time.clock() - self.start_ticks) > 1:
                print(self.name + " finished dawn phase")
                self.start_ticks = -1
                return True
                
    def do_day_phase(self, entities, territories):
        if self.start_ticks == -1:
            self.start_ticks = time.clock()
            print(self.name + " started daytime phase")
        else:
            if (time.clock() - self.start_ticks) > 1:
                print(self.name + " finished daytime phase")
                self.start_ticks = -1
                return True
                
    def do_dusk_phase(self, entities, territories):
        if self.start_ticks == -1:
            self.start_ticks = time.clock()
            print(self.name + " started dusk phase")
        else:
            if (time.clock() - self.start_ticks) > 1:
                print(self.name + " finished dusk phase")
                self.start_ticks = -1
                return True

    def do_night_phase(self, entities, territories):
        if self.start_ticks == -1:
            self.start_ticks = time.clock()
            print(self.name + " started night phase")
        else:
            if (time.clock() - self.start_ticks) > 1:
                print(self.name + " finished night phase")
                self.start_ticks = -1
                return True
                
                
#==============================================================================                

class GameEngine:
    
    def __init__(self, game, max_turns=7):
        self.game = game
        self.max_turns = max_turns
        self.blue_player = None
        self.red_player = None
        self.current_player = None
        self.initialMapState = None
   
    
    def reset(self):
        self.game.reset()
            
        if self.blue_player != None:
            self.blue_player.reset()
            self.blue_player.place_entities(self.game.territories)
            
        if self.red_player != None:
            self.red_player.reset()
            self.red_player.place_entities(self.game.territories)
               
        self.current_player = None
        self.initialMapState = self.storeInitMap()
        self.first_turn()
        
             
#    def printInfo(self):
#      
#      print("printing territories")
#      for territory in self.game.territories.values():
#        civs=territory.get_civilians()
#        a=[]
#        for civilian in civs:
#          #print(territory.name,civilian.name)   
#          a.append(civilian.name)
#        a.sort()
#        print(territory.name,a,self.game.get_surface(territory.name))
#
#
#      #print("printing entities")
#      #a=[]
#      #for e in self.game.entities:
#        #a.append(e)
#      #a.sort()
#      #for e in a:
#        #print(e,self.game.entities[e].territory.name)
#        
#        
#      print("printing entitiesS")
#      a=[]
#      for e in self.game.entitiesS:
#        a.append(e)
#      a.sort()
#      for e in a:
#        if self.game.entitiesS[e].territory==None:
#          print(e,"None")
#        else:
#          print(e,self.game.entitiesS[e].territory.name)

    def set_blue_player(self, player):
        self.blue_player = player
        player.engine = self
        player.side = Side.BLUE
        
        
    def set_red_player(self, player):
        self.red_player = player
        player.engine = self
        player.side = Side.RED

    def first_turn(self):
        if self.game.turn_num == 0:
            self.game.start_turn()
            #from core.model import DO_PRINT
            if Game.DO_PRINT:
                print("---Turn: 1, Phase: DAWN---")
            if self.blue_player != None:
                self.blue_player.start_turn()
                
            if self.red_player != None:
                self.red_player.start_turn()
            
            if self.blue_player != None:
                self.current_player = self.blue_player
            elif self.red_player != None:
                self.current_player = self.red_player
       
           
    def do_phase(self):              
        if self.current_player != None:
            self.current_player.do_phase()

        
    def next_phase(self):
        if self.current_player != None:
            if self.current_player.phase_done:
                if self.game.phase == Phase.DAWN:
                    self.current_player._goto_phase(Phase.DAY, Phase.DAWN)
                    self.game.phase = Phase.DAY
                    return True
                
                elif self.game.phase == Phase.DAY:
                    self.current_player._goto_phase(Phase.DUSK, Phase.DAY)
                    self.game.phase = Phase.DUSK
                    return True
                
                elif self.game.phase == Phase.DUSK:
                    self.current_player._goto_phase(Phase.NIGHT, Phase.DUSK)
                    self.game.phase = Phase.NIGHT
                    
                    if self.red_player != None:
                        self.current_player = self.red_player
                    else:
                        self.current_player = self.blue_player
                    
                    return True
                
                elif self.game.phase == Phase.NIGHT:
                    self.current_player._goto_phase(Phase.DAWN, Phase.NIGHT)
                    self.game.phase = Phase.DAWN
                    
                    if self.blue_player != None:
                        self.current_player = self.blue_player
                    else:
                        self.current_player = self.red_player
                    
                    self.game.end_turn()
                    if self.blue_player != None:
                        self.blue_player.end_turn()
                    if self.red_player != None:
                        self.red_player.end_turn()
                    
                    self.game.start_turn()
                    if self.blue_player != None:
                        self.blue_player.start_turn()
                    if self.red_player != None:
                        self.red_player.start_turn()
                    
                    return True
                
        return False
    

    def do_turn(self):
        self.do_phase()
        return self.next_phase()

             
    def run(self):
        while(self.game.turn_num <= self.max_turns):
            self.do_turn()
    
    
    def storeInitMap(self):
        initialMapState = []
        
        #Metadata for each territory
        for t in self.game.territories:
            tInfo = {}
            tempT = self.game.territories[t]
            tInfo['Name'] = tempT.name 
            tInfo['CivilState'] = tempT.state
            tInfo['Revealed'] = tempT.blue_revealed
            tInfo['NumSupplies'] = len(tempT.supplies)
            tEntities = []
            for a in tempT.airs:
                for e in a.tokens:
                    aData = {}
                    aData['Name'] = e.name
                    aData['Extra'] = ""
                    tEntities.append(aData)
            for l in tempT.lands:
                for e in l.tokens:
                    lData = {}
                    lData['Name'] = e.name
                    if isinstance(e, Civilian):
                        lData['Extra'] = e.state
                    else:
                        lData['Extra'] = ""
                    tEntities.append(lData)
            for s in tempT.seas:
                for e in s.tokens:
                    sData = {}
                    sData['Name'] = e.name
                    sData['Extra'] = s.name
                    tEntities.append(sData)
            tInfo['Entities'] = tEntities
            initialMapState.append(tInfo)

        #Red Entities not allocated to territory at init
        noneInfo = {}
        noneInfo['Name'] = None
        noneEntities = []
        
        if self.red_player != None:
            for redE in self.red_player.entities:
                redEFound = False
                for t in initialMapState:
                    for ent in t['Entities']:
                        if redE.name == ent['Name']: 
                            redEFound = True
                            break
                    if redEFound:
                        break
                #check if fishingboat was not already allocated
                if not redEFound:
                    redEData = {}
                    redEData['Name'] = redE.name
                    if redE.militia:
                        redEData['Extra'] = redE.militia.name
                    else:
                        redEData['Extra'] = ""
                    noneEntities.append(redEData)
        noneInfo['Entities'] = noneEntities
        initialMapState.append(noneInfo)
        return initialMapState
    
    
    def save_state_to_file(self, filePath):
        if filePath != '':
            with open(filePath, 'w') as outFile:
                replayOuput = {}
                replayOuput['0'] = self.initialMapState
                #json prepartion formatting of all the recorded_moves
                for turn in range(self.game.turn_num):
                    nPhase = 4
                    #if the last turn, need to check which phase we ended in
                    if turn+1 == self.game.turn_num:
                        endPhase = self.game.phase
                        if endPhase == 'DAWN':
                            nPhase = 1
                        elif endPhase == 'DAY':
                            nPhase = 2
                        elif endPhase == 'DUSK':
                            nPhase = 3
                        elif endPhase == 'NIGHT':
                            nPhase = 4
                    turnMoves = {}
                    blueMoves = self.blue_player.recorded_moves[turn]
                    redMoves = self.red_player.recorded_moves[turn]
                    #iterate over every phase entered for this turn
                    for p in range(nPhase):
                        phaseMoves = []
                        if p != 3:
                            #BLUE - convert recorded_moves list to a dictionary ready for json
                            for m in range(len(blueMoves[p])):
                                moveData = {}
                                moveData["entity_name"] = blueMoves[p][m][0]
                                moveData["move_label"] = blueMoves[p][m][1]
                                moveData["extra"] = blueMoves[p][m][2]
                                phaseMoves.append(moveData)
                            if p == 0:
                                turnMoves['DAWN'] = phaseMoves
                            elif p == 1:
                                turnMoves['DAY'] = phaseMoves
                            elif p == 2:
                                turnMoves['DUSK'] = phaseMoves
                        else:
                            #RED - convert recorded_moves list to a dictionary ready for json
                            for m in range(len(redMoves[p])):
                                moveData = {}
                                moveData["entity_name"] = redMoves[p][m][0]
                                moveData["move_label"] = redMoves[p][m][1]
                                moveData["extra"] = redMoves[p][m][2]
                                phaseMoves.append(moveData)
                            turnMoves['NIGHT'] = phaseMoves

                    replayOuput[str(turn+1)] = turnMoves
                
                json.dump(replayOuput, outFile, indent=4)
                return True
                
                
        return False
    
    
    def load_state_from_file(self, uploadFile):
        if uploadFile == '':
            #print("Please select a valid file")
            return None
        with open(uploadFile, 'r') as inFile:
            replay = json.load(inFile)
            self.game.replayInit(replay['0'])

            for t in replay['0']:
                if t['Name']:
                    #determine if any supplies need to be spawned
                    newSupplies = []
                    for s in range(t['NumSupplies']):
                        newSupplies.append(Supply())
                    if newSupplies:
                        self.game.territories[t['Name']].add_supplies(newSupplies)
                redEntities = []
                blueEntities = []
                redEntityTypes = ['FishBoat', 'Militia']
                blueEntityTypes = ['C130', 'P8', 'MRH', 'MOTCOY', 'INF', 'MEDIC', 'OPV']
                for e in t['Entities']:
                    #determine which entities to spawn at territory t for each player
                    tokens = e['Name'].split('_')
                    if tokens[0] in blueEntityTypes:
                        blueEntities.append([e['Name'], e['Extra']])
                    elif tokens[0] in redEntityTypes:
                        redEntities.append([e['Name'], e['Extra']])

                if redEntities:
                    self.red_player.create_entities(redEntities, t['Name'])
                if blueEntities:
                    self.blue_player.create_entities(blueEntities, t['Name'])
                    
            
        
            #player.reset(False) is used to indicate not to reset the entities for that player
            self.blue_player.reset(False)
            self.red_player.reset(False)
            
            
            self.initialMapState = self.storeInitMap()
            
            return replay
        
        return None
        

                       