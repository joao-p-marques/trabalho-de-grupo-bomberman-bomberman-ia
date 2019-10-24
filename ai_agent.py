
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

        self.cur_pos = None
        self.walls = None
        self.enemies = None
        self.powerups = None
        self.bonus = None
        self.exit = None
        self.lives = 3 #this shouldnt be hardcoded

        self.pursuing_enemy = None

        # self.TTT = None

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

    def calculate_path(self, origin, goal):
        problem = SearchProblem(self.search_domain, origin, goal)
        tree = SearchTree(problem, strategy='greedy')
        self.logger.info("Searching path from " + str(origin) + " to " + str(goal))
        path, moves = tree.search(depth_limit=self.depth_limit)
        self.logger.debug("Path found.")
        return (path, moves)

    def find_direction(self, path):
        prev_pos = path[0]
        for pos in path:
            if prev_pos[0] < pos[0]: 


    def calculate_path_predict(self, origin, goal=self.pursuing_enemy):
        interesting_moves = goal[1][-5:] # get last 3 positions
        

    def select_bomb_point(self, target):
        closest = None
        for pos in [self.search_domain.result(target, mov) 
                for mov in self.search_domain.actions(target)]:
            d = self.dist(self.cur_pos, pos)
            if closest is None or d < closest[1]:
                closest = (pos, d)

        self.logger.info("Closest wall: " + str(target) + 
                ". Going to " + str(closest[0]))
        
        self.bombpos = closest[0]

        path, moves = self.calculate_path(self.cur_pos, closest[0])
        return (path, moves)

    def hide(self, path, moves):
        # hide in nearby position 
        # but choose the one closest to next wall ? not yet
        possible_moves = [['w', 'a'], 
                          ['w', 'd'], 
                          ['s', 'a'],
                          ['s', 'd'],
                          ['a', 's'],
                          ['a', 'w'],
                          ['d', 'w'],
                          ['d', 's'],
                          ['w', 'w', 'a'],
                          ['w', 'w', 'd'],
                          ['s', 's', 'a'],
                          ['s', 's', 'd'],
                          ['a', 'a', 'w'],
                          ['a', 'a', 's'],
                          ['d', 'd', 'w'],
                          ['d', 'd', 's']
                          ]

        last_pos = path[-1]
        best = None
        for possible_move in possible_moves:
            p = [last_pos]
            this_works = True
            
            #print(last_pos,possible_move)

            if self.can_i_do_this(last_pos, possible_move):
                for move in possible_move:
                    p.append(self.search_domain.result(p[-1], move))
                
                best = (p, possible_move)
                break

            # for move in possible_move:
                
            #     if move in self.search_domain.actions(p[-1]):
            #         p.append(self.search_domain.result(p[-1], move))
            #     else:
            #         this_works = False
            #         break
            # if this_works:
            #     best = (p, possible_move)
            #     break
        
        self.logger.info("Hiding from bomb in " + str(best[0][-1]) + " (" + str(best[1]) + ")")

        path += best[0]
        moves += best[1]
    
    def can_i_do_this(self, pos, possible_move):
        if possible_move == []:
            return True

        letter = possible_move[0]
        #print(pos, letter, letter in self.search_domain.actions(pos))

        return (letter in self.search_domain.actions(pos)) and self.can_i_do_this(
                self.search_domain.result(pos, letter), 
                    possible_move[1:])
        
    def decide_move(self):
        if self.powerups: # powerup to pick up
            powerup = self.powerups.pop(0)[0] # 0 - pos, 1 - type
            self.logger.info("Going for powerup: " + str(powerup))
            path, moves = self.calculate_path(self.cur_pos, powerup)
            return moves
        elif len(self.enemies)>0:
            # go for enemy
            #Os inimigos movem por isso temos que voltar a calcular isto enquanto estamos no  ciclo

            # closest_enemy = self.closest_enemy()
            # self.logger.info("Going for enemy: " + str(closest_enemy))
            # path, moves = self.calculate_path(self.cur_pos, self.closest_enemy()['pos'])
            # moves.append('B')
            # self.hide(path, moves)

            moves=[]
            path = [self.cur_pos]

            closest_enemy = self.closest_enemy()

            # started pursuing different enemy
            if (self.pursuing_enemy is None or 
                    self.pursuing_enemy[0]['id'] != closest_enemy['id']): 
                self.pursuing_enemy = (closest_enemy, [])
            else:
                self.pursuing_enemy[1].append(closest_enemy['pos']) # keep track of enemy movement

            if self.dist(self.cur_pos, closest_enemy['pos']) <= 1 :
                moves.append('B')
                self.hide(path, moves)
                return moves
            elif self.dist(self.cur_pos, closest_enemy['pos']) <= 4: # close enough to predict path
                self.calculate_path_predict(self.cur_pos)
                return moves
            else:
                allpath, allmoves = self.calculate_path(self.cur_pos, closest_enemy['pos'])
                moves.append(allmoves[0])
                return moves

        elif self.exit: # exit is available
            moves=[]
            self.calculate_path(self.cur_pos, self.exit)
            moves.append(allmoves[0])
            return moves
            
        else:
            closest_wall = self.closest_wall()
            path, moves = self.select_bomb_point(closest_wall) 
            moves.append('B') # leave a bomb at the end
            self.hide(path, moves)
            self.search_domain.set_destroyed_wall(closest_wall)
            return moves        

    def next_move(self, state):
        # self.logger.info(state)

        self.cur_pos = state['bomberman']
        self.enemies = state['enemies']
        self.walls = state['walls']
        self.powerups = state['powerups']
        self.bonus = state['bonus']
        self.exit = state['exit']

        lost_life = self.lives != state['lives']
        self.lives = state['lives']

        #Clear after death
        if lost_life:
            self.logger.info("I Died, will restart decisionQueue")
            self.decisions_queue = []
        
        # if self.TTT is None:
        #     self.TTT = self.walls[0]
        # self.logger.debug("TTTTTTT " + str(self.search_domain.map.is_blocked(self.TTT)) + ", " + 
        #         str(self.search_domain.map.is_stone(self.TTT)))

        # if queue is empty and there are no bombs placed
        if not self.decisions_queue and not state['bombs']: 
            self.decisions_queue = self.decide_move()

        if not self.decisions_queue:
            return ''

        self.logger.info("Path: " + str(self.decisions_queue))
        next_move = self.decisions_queue.pop(0)
        self.logger.info("Next move: " + str(next_move))

        return next_move

class BombermanSearch(SearchDomain):

    # construtor
    def __init__(self, map, destroyed_walls=[]):
        self.map = map
        self.logger = logging.getLogger("AI AGENT")
        self.logger.setLevel(logging.DEBUG)
        self.destroyed_walls = destroyed_walls

    def set_destroyed_wall(self, destroyed_wall):
        self.destroyed_walls.append(destroyed_wall)

    # lista de accoes possiveis num estado
    def actions(self, state):
        pos = state
        moves = ['w', 'a', 's', 'd']
        actions_list = []
        
        for move in moves:
            next_pos = self.result(pos, move)
            if ((not self.map.is_blocked(next_pos) and 
                    not self.map.is_stone(next_pos)) or
                    next_pos in self.destroyed_walls):
                actions_list.append(move) 

        return actions_list

    # resultado de uma accao num estado, ou seja, o estado seguinte
    def result(self, state, action):
        if action == 'w':
            return [state[0], state[1]-1]
        if action == 'a':
            return [state[0]-1, state[1]]
        if action == 's':
            return [state[0], state[1]+1]
        if action == 'd':
            return [state[0]+1, state[1]]
        
        #return list(self.map.calc_pos(state, action))

    # custo de uma accao num estado
    def cost(self, state, action):
        return 1

    def dist(self, pos1, pos2):
        return math.hypot(pos2[0]-pos1[0],pos2[1]-pos1[1])

    # custo estimado de chegar de um estado a outro
    def heuristic(self, state, goal_state):
        return self.dist(state, goal_state)

