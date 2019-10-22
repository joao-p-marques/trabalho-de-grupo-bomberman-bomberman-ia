
import json
import logging
import math
import random

from mapa import Map
from tree_search import *

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

class AI_Agent():

    def __init__(self, game_properties):
        self.logger = logging.getLogger("AI AGENT")
        self.logger.setLevel(logging.DEBUG)
        self.logger.info("AI Agent created.")

        self.map = Map(size=game_properties["size"], mapa=game_properties["map"])
        self.logger.info(self.map)

        self.reverse_plays = {"a":"d","w":"s","s":"w","d":"a"}

        self.cur_pos = None
        self.walls = None
        self.enemies = None
        self.depth_limit = 100

        self.search_domain = BombermanSearch(self.map)

        self.decisions_queue = []

    def dist(self, pos1, pos2):
        return math.hypot(pos2[0]-pos1[0],pos2[1]-pos1[1])

    def closest_enemy(self):
        closest = None
        for enemy in self.enemies:
            d = self.dist(self.cur_pos, enemy['pos'])
            if closest is None or d < closest[1]:
                closest = (enemy, d)
        return closest[0] 
    
    #Importante para nao perder tempo a procura de paredes
    def closest_wall(self):
        closest = None
        for wall in self.walls:
            d = self.dist(self.cur_pos, wall)
            if closest is None or d < closest[1]:
                closest = (wall, d)
        return closest[0] 

    # def calculate_path(self, origin, goal, depth=0):
    #     if origin == goal:
    #         return []
    #     if depth > self.depth_limit:
    #         self.logger.debug("Reached recursion depth limit of " + str(self.depth_limit))
    #         return None
    #     move_options = ['w', 'a', 's', 'd']
    #     next_move = None
    #     for move in move_options:
    #         next_pos = self.map.calc_pos(origin, move)
    #         if not self.map.is_blocked(next_pos) and not self.map.is_stone(next_pos):
    #             d = self.dist(next_pos, goal)
    #             if next_move is None or d < next_move[2]:
    #                 next_move = (move, next_pos, d)
    #                 path = self.calculate_path(next_move[1], goal, depth+1)
    #                 if path is None:
    #                     continue
    #                 else:
    #                     self.logger.debug("Path: " + str([next_move] + path))
    #                     return [ next_move ] + path
    #         else: # rollback
    #             self.logger.debug("Rolling back")
    #             return None
    #     return None

    def calculate_path(self, origin, goal):
        problem = SearchProblem(self.search_domain, origin, goal)
        tree = SearchTree(problem, strategy='greedy')
        self.logger.info("Searching path from " + str(origin) + " to " + str(goal))
        path, moves = tree.search(depth_limit=40)
        return (path, moves)

    def hide(self, path, moves):
        pass

    def decide_move(self):
        #if len(self.enemies)>0:
        if False:
            # go for enemy
            #Os inimigos movem por isso temos que voltar a calcular isto enquanto estamos no  ciclo
            closest_enemy = self.closest_enemy()
            self.logger.info("Going for enemy: " + str(closest_enemy))
            return self.calculate_path(self.cur_pos, self.closest_enemy()['pos'])
        else:
            closest_wall = self.closest_wall()

            closest = None
            for pos in [self.search_domain.result(closest_wall, mov) 
                    for mov in self.search_domain.actions(closest_wall)]:
                d = self.dist(self.cur_pos, pos)
                if closest is None or d < closest[1]:
                    closest = (pos, d)

            self.logger.info("Closest wall: " + str(closest_wall) + 
                    ". Going to " + str(closest[0]))

            path, moves = self.calculate_path(self.cur_pos, closest[0])
            moves_after_bomb = moves[-3:]
            moves.append('B') # leave a bomb at the end
            for move in moves_after_bomb:
                moves.append(self.reverse_plays[move])
            return moves

    def next_move(self, state):
        # self.logger.info(state)
        self.cur_pos = state['bomberman']
        self.enemies = state['enemies']
        self.walls = state['walls']
        
        if not self.decisions_queue: # if queue is empty
            self.decisions_queue = self.decide_move()

        self.logger.info("Path: " + str(self.decisions_queue))
        next_move = self.decisions_queue.pop(0)
        self.logger.info("Next move: " + str(next_move))

        return next_move

class BombermanSearch(SearchDomain):

    # construtor
    def __init__(self, map):
        self.map = map
        self.logger = logging.getLogger("AI AGENT")
        self.logger.setLevel(logging.DEBUG)

    # lista de accoes possiveis num estado
    def actions(self, state):
        pos = state
        moves = ['w', 'a', 's', 'd']
        actions_list = []
        for move in moves:
            next_pos = self.result(pos, move)
            if not self.map.is_blocked(next_pos) and not self.map.is_stone(next_pos):
            #if not self.map.is_stone(next_pos):
                actions_list.append(move) 
        return actions_list

    # resultado de uma accao num estado, ou seja, o estado seguinte
    def result(self, state, action):
        return list(self.map.calc_pos(state, action))

    # custo de uma accao num estado
    def cost(self, state, action):
        return 1

    def dist(self, pos1, pos2):
        return math.hypot(pos2[0]-pos1[0],pos2[1]-pos1[1])

    # custo estimado de chegar de um estado a outro
    def heuristic(self, state, goal_state):
        return self.dist(state, goal_state)


# Example output of STATE 

# 2019-10-19 16:40:12,026 - AI AGENT - INFO - {'level': 1, 'step': 55, 'timeout': 3000, 'player': 'jota', 'score': 0, 'lives': 2, 'bomberman': [1, 1], 'bombs': [], 'enemies': [{'name': 'Balloom', 'id': '1a0fb382-61e5-412b-a875-9b2f950f55d5', 'pos': [6, 1]}, {'name': 'Balloom', 'id': '7652ed24-1dd7-4105-bcfd-711318ebf3c0', 'pos': [10, 1]}, {'name': 'Balloom', 'id': '460230f7-6866-4706-8c78-d4cdd10030a7', 'pos': [10, 23]}, {'name': 'Balloom', 'id': '8c508ccd-eba0-4930-a5ea-c4313151015e', 'pos': [11, 23]}, {'name': 'Balloom', 'id': '44526b3b-02c8-4b1e-8245-e29f4e383f13', 'pos': [19, 22]}, {'name': 'Balloom', 'id': 'deda45d7-1d20-45d8-b39d-3e62365072e2', 'pos': [1, 22]}], 'walls': [[3, 11], [3, 24], [3, 29], [4, 3], [5, 26], [6, 21], [7, 23], [10, 11], [10, 27], [11, 4], [11, 7], [12, 21], [12, 25], [13, 7], [13, 29], [14, 15], [15, 4], [17, 18], [17, 20], [19, 11], [21, 17], [21, 28], [23, 3], [24, 7], [24, 25], [25, 3], [25, 5], [25, 20], [26, 9], [27, 15], [27, 19], [28, 15], [29, 10], [29, 28], [30, 17], [30, 19], [35, 6], [35, 14], [35, 19], [35, 20], [35, 23], [36, 15], [37, 12], [38, 7], [39, 11], [39, 27], [40, 9], [40, 13], [41, 4], [41, 25], [45, 12], [46, 17], [46, 29], [48, 11], [48, 17]], 'powerups': [], 'bonus': [], 'exit': []}

