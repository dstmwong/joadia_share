# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 13:28:47 2019

@author: wongm
"""

from core.model import MotCoy, Phase, LiftEntity, FishingBoat, Militia

class Task:
    """
    Top level class Task.
    """
    STATE_FAILED = -1
    STATE_BEGIN = 0
    STATE_RUNNING = 1
    STATE_END = 2
    
    def __init__(self, unit):
        self.unit = unit
        self._state = Task.STATE_BEGIN
        
    def begin(self):
        self._state = Task.STATE_RUNNING
        
    def end(self):
        self._state = Task.STATE_END
        
    def state(self):
        return self._state
        
    def reset(self):
        self._state = Task.BEGIN
        
    def execute(self, phase):
        pass
    
#------------------------------------------------------------------------------

class AStarMove(Task):
    """
    The AStarMove task will move a unit across multiple territories via the 
    shortest calculated A* path. It will only execute during the day phase and
    takes into account the terrain elevation values on movement speed.
    """
    def __init__(self, unit, destination, allowable_phases = [Phase.DAY]):
        super().__init__(unit)
        self.destination = destination
        self.allowable_phases = allowable_phases
        
    def _distance(self, point1, point2):
        import math
        return math.sqrt(pow(point1[0] - point2[0], 2) + pow(point1[1] - point2[1], 2))
        
    def _hscore(self, start, destination):
        if self.unit.move_land:
            return self._distance([start.lands[0].x, start.lands[0].y], [destination.lands[0].x, destination.lands[0].y])
        elif self.unit.move_air:
            return self._distance([start.airs[0].x, start.airs[0].y], [destination.airs[0].x, destination.airs[0].y])
        elif self.unit.move_water:
            return self._distance([start.waters[0].x, start.waters[0].y], [destination.waters[0].x, destination.waters[0].y])
     
    def _minf(self):
        min_val = float("Infinity")
        min_key = None
        for key in self.open_set.keys():
            next_val = self.f_score[key]
            if next_val < min_val:
                min_key = key
                min_val = next_val
        return min_key
    
    def _reconstruct_path(self, came_from, current):
        total_path = [current]
        while current in came_from.keys():
            current = came_from[current]
            total_path.insert(0, current)
        return total_path
        
    def begin(self):
        super().begin()
        
        #astar specific variables
        self.closed_set = {}
        self.open_set = {}
        self.came_from = {}
        self.g_score = {}
        self.f_score = {}
        self.path = []
        
        self.open_set[self.unit.territory] = self.unit.territory
        self.g_score[self.unit.territory] = 0
        start_f = self._hscore(self.unit.territory, self.destination)
        self.f_score[self.unit.territory] = start_f
        
        #calculate the path
        while len(self.open_set.keys()) != 0:
            current = self._minf()
            if current == self.destination:
                self.path = self._reconstruct_path(self.came_from, current)
                #print("start", self.unit.territory.name, "end", self.destination.name, "calculated path", [p.name for p in self.path])
                return
            
            self.open_set.pop(current)
            self.closed_set[current] = current
            
            #get the neighbours of the unit. ie the set of next territories
            #they can move to. This will depend on whether the unit is a land,
            #sea or air unit
            mobility_weight = 1
            if self.unit.move_land:
                neighbours = current.lands[0].connections
            elif self.unit.move_water:
                neighbours = current.seas[0].connections
            elif self.unit_move_air:
                neighbours = current.airs[0].connections
                
            for neighbour in neighbours:
                if neighbour.territory in self.closed_set.keys():
                    continue
               
                if self.unit.move_land:
                    mobility_weight = neighbour.elevation
                    
                tentative_g_score = self.g_score[current] + self._hscore(current, neighbour.territory)*mobility_weight
                               
                if not neighbour.territory in self.open_set.keys():
                    self.open_set[neighbour.territory] = neighbour.territory
                elif tentative_g_score >= self.g_score[neighbour.territory]:
                    continue
                
                self.came_from[neighbour.territory] = current
                self.g_score[neighbour.territory] = tentative_g_score
                self.f_score[neighbour.territory] = self.g_score[neighbour.territory] + self._hscore(current, neighbour.territory)
                
        #if we reached here it means that there is no path to the destination
        #print("start", self.unit.territory.name, "end", self.destination.name, "No path found!")
        self._state = Task.STATE_FAILED
        
        
    def execute(self, phase):
        if self.state() == Task.STATE_RUNNING:
            if phase in self.allowable_phases:
                while True:
                    if self.path != []:
                        #pop the first node on the path if its what we're standing on
                        if self.path[0] == self.unit.territory:
                            self.path.pop(0) 
                        
                        if len(self.path) > 0:
                            next_node = self.path[0]
                        else:
                            self.end()
                            break
                        
                        if self.unit.move_land:
                            if self.unit.movement_points >= next_node.lands[0].elevation:
                                #print(self.unit.name, "moving", next_node.name)
                                #self.unit.move(next_node.lands[0])

                                #PERFORMANCE IMPROVEMENT
                                #Calls to execute_move() use arguments rather than creating a list of parameters
                                #This saves on memory allocation time
                                self.unit.player.execute_move(self.unit.name, "move", next_node.lands[0].name)
                            else:
                                #print("out of movement points")
                                break
                        elif self.unit.move_air:
                            if self.unit.movement_points != 0:
                                #print(self.unit.name, "moving", next_node.name)
                                #self.unit.move(next_node.airs[0])
                                self.unit.player.execute_move(self.unit.name, "move", next_node.airs[0].name)
                            else:
                                #print("out of movement points")
                                break
                        elif self.unit.move_water:
                            if self.unit.movement_points != 0:
                                #print(self.unit.name, "moving", next_node.name)
                                #self.unit.move(next_node.seas[0])
                                self.unit.player.execute_move(self.unit.name, "move", next_node.seas[0].name)
                            else:
                                #print("out of movement points")
                                break
                        else:
                            print("should not reach here")
                            break
                    else:
                        self.end()
         
        return self.state()
                        
#------------------------------------------------------------------------------
                        
class LiftCivilian(Task):
    """
    LiftCivilian Task will lift the civilians in the territory that a LiftEntity unit 
    is currently at. It will lift the maximum number of civilians at any one time.
    """
    def __init__(self, unit):
        super().__init__(unit)
        
    def execute(self, phase):
        if phase == Phase.DAWN and self.state() == Task.STATE_RUNNING:
            if isinstance(self.unit, LiftEntity):
                if not self.unit.is_full():
                    liftables = self.unit.get_liftable_civilians()
                    if liftables != [] and len(liftables) != 0:
                        lift_capacity = self.unit.pax_capacity - self.unit.current_load()
                        liftnum = min(len(liftables), lift_capacity)
                        
                        for i in range(0, liftnum):
                            #PERFORMANCE IMPROVEMENT
                            #Calls to execute_move() use arguments rather than creating a list of parameters
                            #This saves on memory allocation time
                            self.unit.player.execute_move(self.unit.name, "lift PAX", liftables[i].name)
            self.end()
        return self.state()

#------------------------------------------------------------------------------
                        
class DropCivilian(Task):
    """
    DropCivilian task will drop the max number of civilians that a LiftEntity
    is carrying on the territory that it is currently at.
    """
    def __init__(self, unit):
        super().__init__(unit)
        
    def execute(self, phase):
        if phase == Phase.DUSK and self.state() == Task.STATE_RUNNING:
            if isinstance(self.unit, LiftEntity):
                while not self.unit.is_empty():
                    self.unit.player.execute_move(self.unit.name, "drop PAX", self.unit.cargo[0].name)
                super().end()
        return self.state()
    
#------------------------------------------------------------------------------

class LaunchBoat(Task):
    """
    LaunchBoat task allows a player to launch a fishing boat on the JOADIA
    game board
    """
    def __init__(self, unit, territory_name):
        super().__init__(unit)
        self.territory = territory_name
    
    def execute(self, phase):
        if phase == Phase.NIGHT and self.state() == Task.STATE_RUNNING:
            if isinstance(self.unit, FishingBoat):
                self.unit.player.execute_move(self.unit.name, "launch boat", self.territory)
            super().end()
        return self.state()
    
#------------------------------------------------------------------------------

class DeployMilitia(Task):
    """
    DeployMilitia task allows a fishing boat to deploy a militia unit onto
    a territories land surface
    """
    def __init__(self, unit):
        super().__init__(unit)
        
    def execute(self, phase):
        if phase == Phase.NIGHT and self.state() == Task.STATE_RUNNING:
            if isinstance(self.unit, FishingBoat):
                self.unit.player.execute_move(self.unit.name, "deploy militia")
            super().end()
        return self.state()
    
#------------------------------------------------------------------------------

class CauseUnrest(Task):
    """
    CauseUnrest is a task that enables a militia entity to make a city go into
    the unrest state
    """
    def __init__(self, unit):
        super().__init__(unit)
        
    def execute(self, phase):
        if phase == Phase.NIGHT and self.state() == Task.STATE_RUNNING:
            if isinstance(self.unit, Militia):
                self.unit.player.execute_move(self.unit.name, "cause unrest")
            super().end()
        return self.state()
   
#------------------------------------------------------------------------------

class InjurePopulation(Task):
    """
    InjurePopulation is a task that enables a militia entity to injure a civilian
    token. This task will automatically injure up to two civilians.
    """
    def __init__(self, unit):
        super().__init__(unit)
        
    def execute(self, phase):
        if phase == Phase.NIGHT and self.state() == Task.STATE_RUNNING:
            if isinstance(self.unit, Militia):
                self.unit.player.execute_move(self.unit.name, "injure population", 2)
            super().end()
        return self.state()
    
#------------------------------------------------------------------------------

class SabotageSupply(Task):
    """
    SabotageSupply is a task that enables a militia entity to remove all the supplies
    from a territory
    """
    def __init__(self, unit):
        super().__init__(unit)
        
    def execute(self, phase):
        if phase == Phase.NIGHT and self.state() == Task.STATE_RUNNING:
            if isinstance(self.unit, Militia):
                print("executing sabotage supply")
                self.unit.player.execute_move(self.unit.name, "sabotage supply")
            super().end()
        return self.state()
    
#------------------------------------------------------------------------------
 
class NoOp(Task):
    """
    The NoOp task will automatically end the task when executed while not 
    performing any operations required
    """
    def __init__(self, unit):
        super().__init__(unit)
        
    def execute(self, phase):
        super().end()
        return self.state()

#------------------------------------------------------------------------------
        
class CompositeTask(Task):
    """
    CompositeTask is a container for a sequence of tasks to be performed. Tasks
    must finish successfully for the next task to start. Otherwise the entire
    sequence of tasks in CompositeTask will fail.
    """
    def __init__(self, unit):
        super().__init__(unit)
        self.current_task = None
        self.tasks = []
        self.current_task_index = -1
    
    def add_task(self, task):
        self.tasks.append(task)
    
    def set_task(self, task):
        if self.current_task != None:
            self.current_task.end()
        
        self.current_task_index = -1
        self.tasks.clear()
        self.add_task(task)
        self.begin()
           
    def begin(self):
        self.current_task_index = -1
        super().begin()
        
    def _update_state(self):
        if self.current_task == None or self.current_task.state() == Task.STATE_END:
            if self.tasks != [] and self.current_task_index < len(self.tasks)-1:
                self.current_task_index += 1
                self.current_task = self.tasks[self.current_task_index]
                self.current_task.begin()
            else:
                self.current_task = None
                self.end()
                
        elif self.current_task.state() == Task.STATE_FAILED:
            self.current_task = None
            self._state = Task.STATE_FAILED
    
    def execute(self, phase):
        self._update_state()
        if self.current_task != None:
            self.current_task.execute(phase)
            self._update_state()
        
        
                

#------------------------------------------------------------------------------

class MoveCivilian(CompositeTask):
    """
    The MoveCivilian task is a high level task that moves a unit from a source
    territory, collects civilians from the source territory, move to the 
    destination territory and drops off the civilians to the destination 
    territory
    """
    def __init__(self, unit, source, destination):
        super().__init__(unit)
        self.source = source
        self.destination = destination
        self.add_task(AStarMove(unit, source))
        self.add_task(LiftCivilian(unit))
        self.add_task(AStarMove(unit, destination))
        self.add_task(DropCivilian(unit))
     

#------------------------------------------------------------------------------

class DropMilitiaTask(CompositeTask):
    """
    The DropMilitiaTask enables a fishing boat to move to a destination territory
    and drop off a militia entity
    """
    def __init__(self, unit, dest_territory):
        super().__init__(unit)
        self.destination = dest_territory
        self.add_task(AStarMove(unit, dest_territory))
        self.add_task(DeployMilitia(unit))
        
#------------------------------------------------------------------------------

class CauseUnrestTask(CompositeTask):
    """
    The CauseUnrestTask enables a militia entity to move to a destination territory
    and cause unrest within a population
    """
    def __init__(self, unit, dest_territory):
        super().__init__(unit)
        self.destination = dest_territory
        self.add_task(AStarMove(unit, dest_territory, [Phase.NIGHT]))
        self.add_task(CauseUnrest(unit))
     

#------------------------------------------------------------------------------

class InjurePopulationTask(CompositeTask):
    """
    The InjurePopulationTask enables a militia entity to move to a destination territory
    and injure a civilian entity within that territory
    """
    def __init__(self, unit, dest_territory):
        super().__init__(unit)
        self.destination = dest_territory
        self.add_task(AStarMove(unit, dest_territory, [Phase.NIGHT]))
        self.add_task(InjurePopulation(unit))
        
#------------------------------------------------------------------------------    

class SabotageSupplyTask(CompositeTask):
    """
    The SabotageSupplyTask enables a militia entity to move to a destination
    territory and remove all the supplies from that territory
    """
    def __init__(self, unit, dest_territory):
        super().__init__(unit)
        self.destination = dest_territory
        self.add_task(AStarMove(unit, dest_territory, [Phase.NIGHT]))
        self.add_task(SabotageSupply(unit))
