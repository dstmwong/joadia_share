# -*- coding: utf-8 -*-
"""
Created on 21/01/2019
Testing beam search
@author: kamenetsd
"""

from core.engine import GameEngine, Player, TimerPlayer, HumanPlayer
from core.model import Game, MotCoy, LiftEntity, C130, MobileEntity, OPV, MRH, P8, Inf, Medic, Militia, FishingBoat, Population, Side, Supply, Civilian, Phase
from core.environment import create_territories
from core.pysimplegui_ui import JoadiaWindowApp
from ai.random_ai import RandomRedAI, RandomBlueAI, CyclingRedAI
from ai.beamSearch_ai import BeamSearchBlueAI
import sys
import random


def gameScore(engine):
  rescues=engine.game.rescues
  deaths=engine.game.deaths 
  
  return 2*rescues-deaths


#test replaying capability
def test():
   
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

  
  #blueplayer = RandomBlueAI("BluePlayer")
  blueplayer = BeamSearchBlueAI("BeamSearchBluePlayer")
  blueplayer.side = Side.BLUE
  blueplayer.set_entities([MotCoy(), MotCoy(), OPV(), 
                          OPV(), C130(), P8(), Inf(), 
                          Inf(), Medic(), Medic()])
    
  #blueplayer.set_entities([C130(),MotCoy(), MotCoy(), OPV()])

  #redplayer = RandomRedAI("RedPlayer")
  #redplayer.side = Side.RED
  #redplayer.set_entities([FishingBoat(Militia()), FishingBoat(), 
                          #FishingBoat(Militia()), FishingBoat(), 
                          #FishingBoat(Militia()), FishingBoat(), 
                          #FishingBoat(Militia()), FishingBoat()])  

  engine.add_player(blueplayer)
  #engine.add_player(redplayer)

  badCount=0
  
  for i in range(100):
    #if (i%1000==0): print(i)
    
    engine.reset()
    blueplayer.moves=[]
    if i==0: blueplayer.updateEntitiesS()
    engine.current_player.mode="random"
    engine.run()    
    
    #print("------------")    

    rescues=engine.game.rescues
    deaths=engine.game.deaths
    moves=blueplayer.moves
    #print(moves)
    
    engine.reset()
    engine.current_player.mode="replay"
    engine.current_player.moves=moves
    engine.run()    

    rescues2=engine.game.rescues
    deaths2=engine.game.deaths    
    
    if rescues!=rescues2 or deaths!=deaths2:
      print("game mismatch",rescues,deaths,rescues2,deaths2)
      badCount+=1
    else:
      print("results match!!!",rescues,deaths)
      

  print("bad count",badCount)  


def beamSearch():
  debug=True
  
  #parameters to beam search
  beamSize=10
  mult=10
  
  runs=beamSize*mult
  bestScore=-1000000000
  prevCutoff=bestScore
  
   
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

  
  blueplayer = BeamSearchBlueAI("BeamSearchBluePlayer")
  blueplayer.side = Side.BLUE
   
  blueplayer.set_entities([MotCoy(), MotCoy(), OPV(), 
                          OPV(), C130(), P8(), Inf(), 
                          Inf(), Medic(), Medic()])   
      
  #------------------------------------------------------------------------------
        
  engine.set_blue_player(blueplayer)


  
  Q=[]    #list of moves sorted by score
  
  for turn in range(0, engine.max_turns):          #0 to 7
    
    #cull the Q to the top items
    if turn>0:
      total=0
      
      print("Q size "+str(len(Q)))
      
      Q.sort(reverse=True)        #sort from largest to smallest
      Q=Q[0:beamSize]
      
      for i in range(beamSize):
        score=Q[i][0]
        prevCutoff=score
        total+=score
        if i<5 or i==beamSize-1:
          print(str(i)+" score "+str(score))
        #print(str(i)+" score "+str(score)+" "+str(Q[i][1][0][0][0:3]))
        
      print("average "+str(total/beamSize))
      print()
        
       
    
    for run in range(runs):
      
      if turn==0:
        moves=[]
        units=[]
      else:
        a=random.choice(Q)
        moves=a[1]
        moves=moves[0:turn]
        units=a[2]
        
      
      blueplayer.mode="both"
      blueplayer.moves=moves     
      blueplayer.Units=units      
      engine.reset()
      if turn==0: blueplayer.updateEntitiesS()      
      #engine.current_player.mode="both"
      #engine.current_player.moves=moves     
      #engine.current_player.Units=units      
      #engine.current_player.doEntities()
      engine.run()        
            
      score=gameScore(engine)
      
      #add to Q if the score is good enough
      if score>prevCutoff:
        Q.append((score, moves, engine.current_player.Units))
        
      
      if score>bestScore:
        bestScore=score
        rescues=engine.game.rescues
        deaths=engine.game.deaths 
        print("Fixed "+str(turn)+" run "+str(run)+"/"+str(runs))
        print("score "+str(score)+" rescued "+str(rescues)+" deaths "+str(deaths))
        engine.current_player.printUnits()
        #print(moves)
        print("Fixed "+str(turn)+" run "+str(run)+"/"+str(runs))
        print("score "+str(score)+" rescued "+str(rescues)+" deaths "+str(deaths))        
        print()      
        sys.stdout.flush()    #need to flush buffer for printing to work correctly    
        
  blueplayer.mode = "replay"
  # window = JoadiaWindowApp(engine)
  # window.map_view.auto_update = False
  # window.run()

#-------------------------------------------


#test()
beamSearch()







