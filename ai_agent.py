
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
        # self.eval_enemy = None

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

    def find_direction(self, prev_pos, pos):
        if prev_pos[0] < pos[0]: 
            return 'd'
        elif prev_pos[0] > pos[0]:
            return 'a'
        elif prev_pos[1] < pos[1]:
            return 'w'
        elif prev_pos[1] > pos[1]:
            return 's'

    def opposite_move(self, move):
        if move == 'w':
            return 's'
        elif move == 's':
            return 'w'
        elif move == 'a':
            return 'd'
        elif move == 'd':
            return 'a'

    def running_away(self, move):
        # self.logger.debug(str(self.pursuing_enemy))
        if (self.find_direction(self.pursuing_enemy['last_pos'], self.pursuing_enemy['pos']) == move 
                and ((self.cur_pos[0] == self.pursuing_enemy['pos']) 
                    or (self.cur_pos[1] == self.pursuing_enemy['pos']))):
            self.logger.info("Enemy running away from me.")
            return True
        return False

    def running_towards(self, move):
        if (not 'last_pos' in self.pursuing_enemy 
                or self.pursuing_enemy['last_pos'] is None 
                or self.pursuing_enemy is None):
            return False
        self.logger.debug(str(self.pursuing_enemy))
        if (self.find_direction(
            self.pursuing_enemy['last_pos'], 
            self.pursuing_enemy['pos']
            ) == self.opposite_move(move)
                and ((self.cur_pos[0] == self.pursuing_enemy['pos'][0]) 
                    or (self.cur_pos[1] == self.pursuing_enemy['pos'][1]))):
            self.logger.info("Enemy running towards me.")
            return True
        return False

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

            path = self.result(possible_move)
            if len(self.enemies) > 0 and self.closest_enemy()['pos'] in path:
                continue

            p = [last_pos]
            this_works = True
            
            #print(last_pos,possible_move)

            if self.can_i_do_this(last_pos, possible_move):
                for move in possible_move:
                    p.append(self.search_domain.result(p[-1], move))
                
                best = (p, possible_move)
                break
        
        self.logger.info("Hiding from bomb in " + str(best[0][-1]) + " (" + str(best[1]) + ")")

        path += best[0]
        moves += best[1]

    def result(self, moves, origin=None):
        if origin is None:
            origin = self.cur_pos
        path = [origin]
        for mov in moves:
            r = self.search_domain.result(path[-1], mov)
            path.append(r)
        return path
    
    def can_i_do_this(self, pos, possible_move):
        if possible_move == []:
            return True

        enemies_pos = []
        for e in self.enemies:
            enemies_pos.append(e['pos'])

        letter = possible_move[0]
        #print(pos, letter, letter in self.search_domain.actions(pos))

        return ((letter in self.search_domain.actions(pos))
                and self.can_i_do_this(
                    self.search_domain.result(pos, letter), 
                        possible_move[1:]))

    def predict_enemy(self, n_moves, enemy=None):
        if enemy is None:
            enemy = self.pursuing_enemy

        if 'last_pos' in enemy:
            direction = self.find_direction(enemy['last_pos'], enemy['pos'])
            moves = [direction for _ in range(n_moves)]
            result = self.result(moves, enemy['pos'])
            return result
        else:
            return None
        
    def decide_move(self):
        if self.powerups: # powerup to pick up
            powerup = self.powerups.pop(0)[0] # 0 - pos, 1 - type
            self.logger.info("Going for powerup: " + str(powerup))
            path, moves = self.calculate_path(self.cur_pos, powerup)
            return moves
        elif len(self.enemies)>0:
            # go for enemy
            #Os inimigos movem por isso temos que voltar a calcular isto enquanto estamos no  ciclo

            # moves=[]
            # path = [self.cur_pos]

            # self.eval_enemy = True

            closest_enemy = self.closest_enemy()

            # started pursuing different enemy
            if (self.pursuing_enemy is None or 
                    self.pursuing_enemy['id'] != closest_enemy['id']): 
                self.pursuing_enemy = closest_enemy
                self.pursuing_enemy['last_pos'] = None
            else:
                last_pos = self.pursuing_enemy['pos'] # keep track of enemy movement
                self.pursuing_enemy = closest_enemy
                self.pursuing_enemy['last_pos'] = last_pos

            # if self.decisions_queue:
            #     self.loggger.debug("Already have queue")
            #     moves = self.decisions_queue
            #     path = self.result(moves)
            # else:
            #     path, moves = self.calculate_path(self.cur_pos, closest_enemy['pos'])
            #     mov = moves[0]

            path, moves = self.calculate_path(self.cur_pos, closest_enemy['pos'])
            # mov = moves[0]

            if self.dist(self.cur_pos, closest_enemy['pos']) <= 2:
                if self.running_towards(moves[0]):
                    moves = ['B']
                    self.hide([self.cur_pos], moves)
                    return moves
            if self.dist(self.cur_pos, closest_enemy['pos']) <= 2:
                moves = ['B']
                self.hide([self.cur_pos], moves)
                return moves
            else:
                return [moves[0]]

            # elif self.dist(self.cur_pos, closest_enemy['pos']) <= 2:
            #     if self.pursuing_enemy['last_pos'] is not None:
            #         if self.running_away(mov): # enemy running away so keep going
            #             # moves = ['B', mov]
            #             # self.hide([self.cur_pos, path[0]], moves)
            #             return moves
            #         elif self.running_towards(mov): # enemy running towards me so run away
            #             moves = [self.opposite_move(mov), 'B']
            #             path = [self.cur_pos, self.search_domain.result(self.cur_pos, moves[0])]
            #             self.hide(path, moves)
            #             return moves

        elif self.exit: # exit is available
            # self.eval_enemy = False
            path, moves = self.calculate_path(self.cur_pos, self.exit)
            return moves
            
        else:
            # self.eval_enemy = False
            closest_wall = self.closest_wall()
            path, moves = self.select_bomb_point(closest_wall) 
            moves.append('B') # leave a bomb at the end
            self.hide(path, moves)
            return moves        

    def next_move(self, state):
        # self.logger.info(state)

        self.cur_pos = state['bomberman']
        self.enemies = state['enemies']
        self.powerups = state['powerups']
        self.bonus = state['bonus']
        self.exit = state['exit']
        #self.walls = state['walls']

        #Workaround to compare previous and current walls
        new_walls = state['walls']
        if self.walls is not None:
            for wall in [w for w in new_walls if w not in self.walls]:
                self.search_domain.set_destroyed_wall(wall)
        self.walls = new_walls

        #destroyed_walls = []
        #if finalWalls != None and self.walls != None:
        #    initialWalls = self.walls
        #    self.logger.info("FinalWalls: \n%s, \nInitialwalls: \n%s" % (finalWalls,initialWalls))
        #    #destroyed_walls = list( set(initialWalls) - set(finalWalls) )
        #    for wall in destroyed_walls:
        #        self.search_domain.set_destroyed_wall(wall)

        # self.walls = finalWalls

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
        if (not self.decisions_queue) and not state['bombs']: 
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

    #Alterar para isto
    def set_destroyed_wall(self, destroyed_wall):
        self.map.remove_wall(destroyed_wall)

    # lista de accoes possiveis num estado
    def actions(self, state):
        pos = state
        moves = ['w', 'a', 's', 'd']
        actions_list = []
        
        for move in moves:
            next_pos = self.result(pos, move)
            if ((not self.map.is_blocked(next_pos) and 
                    not self.map.is_stone(next_pos))):
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
        # return math.hypot(pos2[0]-pos1[0],pos2[1]-pos1[1])
        return abs(pos2[0]-pos1[0]) + abs(pos2[1]-pos1[1])

    # custo estimado de chegar de um estado a outro
    def heuristic(self, state, goal_state):
        return self.dist(state, goal_state)

