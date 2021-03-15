import random

import gym
from gym import spaces
from gym.utils import seeding
import numpy as np

from ai.heuristic_ai import DefaultHeuristic, DoNothingHeuristic, BestCaseHeuristic2, HillClimbingPolicy3
from core.model import Game, MotCoy, C130, OPV, Side, P8, Medic, Inf, MRH, Phase, LiftEntity, Population, Civilian, \
    Supply, Surface, MobileEntity


class Action():
    def __init__(self, entity, description, surface):
        self.entity = entity
        self.description = description
        self.surface = surface

    def __eq__(self, other):
        return (self.entity, self.description, self.surface) == (other.entity, other.description, other.surface)

    def __hash__(self):
        return hash((self.entity, self.description, self.surface))

    def __str__(self):
        return str(self.get_action_list())

    def __repr__(self):
        return str(self.get_action_list())

    def get_action_list(self):
        return [self.entity.name, self.description, self.surface.name]


class JoadiaEnv(gym.Env):
    def __init__(self, engine, actionable_entities):
        self.engine = engine
        self.bonus_weight = 1
        self.current_entity_index = 0
        self.support_heuristic_player = HillClimbingPolicy3()
        self.support_heuristic_player.engine = self.engine

        self.actionable_entities = actionable_entities
        self.unactioned_entities = []
        self.action_id_to_actions_map = {}
        self.action_to_action_id_map = {}
        self.enumerate_territories()
        self.create_surface_id_map()
        self.individual_actions = False
        self.enumerate_actions()
        self.phases = {"DAWN": 0, "DAY": 1, "DUSK": 2, "NIGHT": 3}

        self.training = True
        self.train_score_history = []
        self.eval_score_history = []

        self.reset()
        self.setup()
        self.seed()

    def setup(self):
        number_of_actions = len(self.action_id_to_actions_map)
        self.action_space = spaces.Discrete(number_of_actions)
        observation = self.get_observation()
        low = np.zeros(len(observation))
        high = np.full(len(observation), number_of_actions - 1)
        self.observation_space = spaces.Box(low, high, dtype=np.float32)

    def seed(self, seed=None):
        np_random, seed = seeding.np_random(seed)
        return [seed]

    def step(self, action):
        observation, reward, done = self.do_step(action)
        return observation, reward, done, {}

    def reset(self):
        # Need to reset the populations each game
        for territory in self.engine.game.territories:
            self.engine.game.territories[territory].civilians.clear()

        self.engine.reset()
        self.current_entity_index = 0

        if self.engine.game.phase == Phase.DAWN:
            self.support_heuristic_player.do_dawn_phase(self.engine.current_player.entities, self.engine.game.territories)
            self.progress_phase()
        self.unactioned_entities = self.engine.blue_player.entities[:]

        return self.get_observation()

    def render(self, mode='human'):
        pass

    def close(self):
        pass

    def do_step(self, action_index):
        initial_score = self.engine.game.get_score()
        action = self.get_action_from_action_id(action_index)

        entity = action.entity
        action_list = action.get_action_list()

        shaped_reward = 0
        territory = action.surface.territory
        if isinstance(entity, LiftEntity) and not territory.has_pod():
            healthy_civs = [civ for civ in territory.civilians.values() if civ.alive and civ.state == Civilian.HEALTHY]
            shaped_reward = len(healthy_civs)
            for actionable_entity in self.actionable_entities:
                if entity != actionable_entity and isinstance(actionable_entity, LiftEntity) and actionable_entity.territory == territory:
                    shaped_reward -= actionable_entity.pax_capacity

        if self.engine.game.phase != Phase.DAY:
            raise Exception("Error - step function only supports day phases.")

        self.engine.current_player.execute_move(action_list[0], action_list[1], action_list[2])
        entity.movement_points = 0

        game_done = False
        while True:
            self.current_entity_index += 1
            if self.current_entity_index >= len(self.engine.current_player.entities):
                # We have finished all entities for the day phase, we need to progress to the next day phase
                game_done = self.jump_to_next_day_phase()
                self.current_entity_index = 0
                if game_done:
                    break

            entity = self.engine.current_player.entities[self.current_entity_index]

            # Decide whether to use Heuristics in a number of special cases.
            use_heuristic_mrh = isinstance(entity, MRH) and self.engine.game.turn_num % 2 == 0  # Set to False to turn off
            use_even_turns_heuristic = isinstance(entity, LiftEntity) and self.engine.game.turn_num % 2 == 0
            use_heuristic = use_heuristic_mrh or use_even_turns_heuristic

            if entity in self.actionable_entities and self.engine.game.turn_num < 7 and not use_heuristic:
                break
            else:
                self.support_heuristic_player.do_day_phase([entity], self.engine.game.territories)

        # reward = current_score - initial_score
        reward = shaped_reward
        # reward = 0
        if game_done:
            reward = self.engine.game.get_score()
        return self.get_observation(), reward, game_done

    def jump_to_next_day_phase(self):
        game_done = False
        self.progress_phase()
        self.support_heuristic_player.do_dusk_phase(self.engine.current_player.entities, self.engine.game.territories)
        self.progress_phase()
        self.support_heuristic_player.do_night_phase(self.engine.current_player.entities, self.engine.game.territories)
        self.progress_phase()
        if self.engine.game.turn_num > self.engine.max_turns:
            if self.training:
                self.train_score_history.append(self.engine.game.get_score())
            else:
                self.eval_score_history.append(self.engine.game.get_score())
            game_done = True
        if not game_done:
            self.support_heuristic_player.do_dawn_phase(self.engine.current_player.entities,
                                                        self.engine.game.territories)
            self.progress_phase()
        return game_done

    def get_civilians_moved_to_fob(self, action):
        if action[1] == "move":
            territory = self.engine.game.surfaces[action[2]].territory
            entity = self.engine.game.entities[action[0]]
            if isinstance(entity, LiftEntity) and entity.carry_mode == "PAX":
                if territory.has_pod():
                    return len(entity.cargo)
                elif not territory.has_pod():
                    return -len(entity.cargo)
        return 0

    def enumerate_actions(self):
        action_id = 0
        self.action_id_to_actions_map = {}
        self.action_to_action_id_map = {}
        self.surface_id_to_action_id_map = {}
        for entity in self.actionable_entities:
            for surface_str in self.engine.game.surfaces:
                surface = self.engine.game.surfaces[surface_str]
                if ((entity.move_land and surface.mobility_type == Surface.LAND) or
                    (entity.move_water and surface.mobility_type == Surface.WATER) or
                    (entity.move_air and surface.mobility_type == Surface.AIR)):
                    action = Action(entity, "move", surface)
                    if self.individual_actions:
                        self.action_id_to_actions_map[action_id] = [action]
                        self.action_to_action_id_map[action] = action_id
                        action_id +=1
                    else:
                        if surface.surface_id[0] in self.surface_id_to_action_id_map:
                            act_id = self.surface_id_to_action_id_map[surface.surface_id[0]]
                        else:
                            self.surface_id_to_action_id_map[surface.surface_id[0]] = action_id
                            act_id = action_id
                            action_id += 1
                        if act_id in self.action_id_to_actions_map:
                            self.action_id_to_actions_map[act_id].append(action)
                        else:
                            self.action_id_to_actions_map[act_id] = [action]
                        self.action_to_action_id_map[action] = act_id

    def enumerate_territories(self):
        territory_id = 0
        for territory in self.engine.game.territories:
            self.engine.game.territories[territory].territory_id = territory_id
            territory_id += 1

    def create_surface_id_map(self):
        sea_surfaces = []
        self.surface_names_to_surfaces_map = {}
        self.surface_id_to_surfaces_map = {}

        for surface_name in self.engine.game.surfaces:
            self.surface_names_to_surfaces_map[surface_name] = self.engine.game.surfaces[surface_name]
            if self.engine.game.surfaces[surface_name].mobility_type == Surface.WATER:
                sea_surfaces.append(surface_name)

        for id, surface_name in enumerate(sea_surfaces):
            s_string = surface_name
            territory_number = s_string.split("_")[0][1:]
            l_string = "L" + territory_number
            a_string = "A" + territory_number
            for temp_surface_name in self.engine.game.surfaces:
                if temp_surface_name == s_string or temp_surface_name == l_string or temp_surface_name == a_string:
                    if not hasattr(self.engine.game.surfaces[temp_surface_name],"surface_id"):
                        self.engine.game.surfaces[temp_surface_name].surface_id = [id]
                    else:
                        self.engine.game.surfaces[temp_surface_name].surface_id.append(id)

                    if id in self.surface_id_to_surfaces_map:
                        self.surface_id_to_surfaces_map[id].append(self.engine.game.surfaces[temp_surface_name])
                    else:
                        self.surface_id_to_surfaces_map[id] = [self.engine.game.surfaces[temp_surface_name]]

    def get_valid_action_indices(self, observation):
        valid_action_indexes = []
        if self.engine.current_player:
            current_entity_index = observation[1]
            current_entity = self.engine.current_player.entities[current_entity_index]
            if current_entity in self.actionable_entities:
                valid_surfaces = self.find_reachable_locations(current_entity)
                for surface in valid_surfaces:
                    action = Action(current_entity, "move", self.surface_names_to_surfaces_map[surface])
                    action_index = self.action_to_action_id_map[action]
                    valid_action_indexes.append(action_index)
        return valid_action_indexes

    def get_action_from_action_id(self, action_id):
        candidate_actions = self.action_id_to_actions_map[action_id]
        if len(candidate_actions)==1:
            return candidate_actions[0]
        for action in candidate_actions:
            if action.entity == self.engine.current_player.entities[self.current_entity_index]:
                return action
        raise Exception("Error - Called get_action_from_action_id({}) but there were no actions for the entity at entity_index {}".format(action_id, self.current_entity_index))

    def find_reachable_locations(self, entity):
        mobility_type = None
        if entity.move_land:
            mobility_type = Surface.LAND
        elif entity.move_water:
            mobility_type = Surface.WATER
        elif entity.move_air:
            mobility_type = Surface.AIR
        locations = set()
        self.search_connections(entity.surface, entity.max_movement_points, mobility_type, locations)
        sorted_locations = list(locations)
        sorted_locations.sort()
        return sorted_locations

    def search_connections(self, surface, movement_points, mobility_type, locations):
        for connection in surface.connections:
            if connection.mobility_type == mobility_type and movement_points >= connection.elevation:
                locations.add(connection.name)
                self.search_connections(connection, movement_points - connection.elevation, mobility_type, locations)

    def get_observation(self):
        # Return an observation of the current game state in the specified format
        # Observation Type 1: observation = [self.engine.game.turn_num, self.current_entity_index]
        # Observation Type 2: observation = [self.engine.game.turn_num, self.current_entity_index, entity.surface.surface_id[0]]

        observation = [self.engine.game.turn_num, self.current_entity_index]
        for entity_key in self.engine.game.entities:
            entity = self.engine.game.entities[entity_key]
            if entity in self.actionable_entities:
                territory_id = int(entity.territory.name[1:])
                observation.append(territory_id)

        # CIVILIAN INFORMATION IN THE OBSERVATION - ONLY REQUIRED FOR DYNAMIC SOLUTIONS
        # for surface_key in self.engine.game.surfaces:
        #     surface = self.engine.game.surfaces[surface_key]
        #     if surface.mobility_type == Surface.LAND:
        #         if surface.territory.blue_revealed:
        #             healthy_count = 0
        #             injured_count = 0
        #             for token in surface.tokens:
        #                 if isinstance(token, Civilian):
        #                     if token.state == Civilian.HEALTHY:
        #                         healthy_count += 1
        #                     elif token.state == Civilian.INJURED:
        #                         injured_count += 1
        #             observation.append(healthy_count)
        #             observation.append(injured_count)
        #         else:
        #             observation.append(-1)
        #             observation.append(-1)
        return observation

    def progress_phase(self):
        self.engine.current_player.phase_done = True
        self.engine.next_phase()