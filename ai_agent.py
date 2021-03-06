
import json
import logging
import sys
import math
import random

from mapa import Map
from tree_search import *

file_handler = logging.FileHandler(filename='ai_agent.log',mode='w+')
stdout_handler = logging.StreamHandler(sys.stdout)
# handlers = [file_handler, stdout_handler]
handlers = [stdout_handler]
logging.basicConfig(
	level=logging.WARN, 
	format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
	handlers=handlers
)

class AI_Agent():

    def __init__(self, game_properties):
        self.logger = logging.getLogger("AI AGENT")
        self.logger.setLevel(logging.WARN)
        self.logger.info("AI Agent created.")

        self.map = Map(size=game_properties["size"], mapa=game_properties["map"])
        self.logger.debug(self.map)

        self.update_wallpass_next = False
        self.cur_pos = None
        self.walls = None
        self.enemies = None
        self.powerups = None
        self.bonus = None
        self.exit = None
        self.have_powerup = None
        self.level = None
        self.lives = 3 #this shouldnt be hardcoded

        # self.enemy_past_pos = {}
        self.pursuing_enemy = None
        # self.eval_enemy = None

        self.depth_limit = 100
        self.loop = 0
        self.search_domain = BombermanSearch(self.map)

        self.decisions_queue = []

        self.rounds_pursuing_limit = 3 # Limit of rounds we can be pursuing the same enemy
        self.wait_time = 200 # time to wait when in loop pursuing enemy

        self.last_enemy_dir = None
        self.perform_last_resort = False


    def dist(self, pos1, pos2):
        return math.hypot(pos2[0]-pos1[0],pos2[1]-pos1[1])

    def update_pursuing_enemy(self, closest_enemy):
        if (self.pursuing_enemy is None 
            or self.pursuing_enemy['id'] != closest_enemy['id']): 
            self.pursuing_enemy = closest_enemy
            self.pursuing_enemy['last_pos'] = None
            self.pursuing_enemy['rounds_pursuing'] = 0
            self.reset_waiting_limit()
        else:
            last_pos = self.pursuing_enemy['pos'] # keep track of enemy movement
            rounds_pursuing = self.pursuing_enemy['rounds_pursuing']
            self.pursuing_enemy = closest_enemy
            self.pursuing_enemy['last_pos'] = last_pos
            self.pursuing_enemy['rounds_pursuing'] = rounds_pursuing 

    def incr_round(self):
        rounds_pursuing = self.pursuing_enemy['rounds_pursuing']
        self.pursuing_enemy['rounds_pursuing'] = rounds_pursuing + 1

    def reset_life(self):
        self.logger.info("I Died, will restart decisionQueue------------------------------------------")
        #self.cur_pos = [1,1]
        self.decisions_queue = []

    def reset_level(self):
        self.logger.info("NEW LEVEL")
        #self.cur_pos = [1,1]
        self.decisions_queue = []
        self.have_powerup = False
        self.pursuing_enemy = None
        self.search_domain.remove_destroyed_walls()

    def reset_waiting_limit(self):
        if self.level > 2:
            self.rounds_pursuing_limit = 4 # Limit of rounds we can be pursuing the same enemy
            self.wait_time = 70 # time to wait when in loop pursuing enemy
        elif self.level > 6:
            self.wait_time = 50
            self.rounds_pursuing = 5

    def update_level(self, level):
        if self.level is None:
            self.level = level
        if self.level != level:
            self.reset_level()
            self.reset_map_walls()
        self.level = level

    def reset_map_walls(self):
        self.logger.debug("Updating walls because NEXT LEVEL")
        self.search_domain.set_walls(self.walls)

    def closest_enemy(self, pos=None):
        if pos is None:
            pos = self.cur_pos
        closest = None
        for enemy in self.enemies:
            d = self.dist(pos, enemy['pos'])
            if closest is None or d < closest[1]:
                closest = (enemy, d)
        return closest[0] if closest != None else None
    
    #Importante para nao perder tempo a procura de paredes
    def closest_wall(self, i=0):
        closest_list = []
        if not self.walls:
            return None
        for wall in self.walls:
            d = self.dist(self.cur_pos, wall)
            closest_list.append((wall, d))
            # if closest is None or d < closest[1]:
            #     closest = (wall, d)
        closest_list = sorted(closest_list, key=lambda x:x[1])
        return closest_list[i][0]

    def calculate_path(self, origin, goal):
        problem = SearchProblem(self.search_domain, origin, goal)
        tree = SearchTree(problem, strategy='greedy')
        self.logger.debug("Searching path from " + str(origin) + " to " + str(goal))
        # self.logger.debug(self.walls)
        path, moves = tree.search(depth_limit=self.depth_limit)
        self.logger.debug("Path found.")
        return (path, moves)

    def find_direction(self, prev_pos, pos):
        #change this
        if prev_pos is None:
            return ''
        if prev_pos[0] < pos[0]: 
            return 'd'
        elif prev_pos[0] > pos[0]:
            return 'a'
        elif prev_pos[1] > pos[1]:
            return 'w'
        elif prev_pos[1] < pos[1]:
            return 's'

    def dir_in_x(self, d):
        if d in ['a', 'd']:
            return True
        return False

    def dir_in_y(self, d):
        if d in ['w', 's']:
            return True
        return False

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
        enemy_dir = self.find_direction(self.pursuing_enemy['last_pos'], self.pursuing_enemy['pos'])

        cond1 = self.dir_in_x(enemy_dir) and (self.cur_pos[1] == self.pursuing_enemy['pos'][1])
        cond2 = self.dir_in_y(enemy_dir) and (self.cur_pos[0] == self.pursuing_enemy['pos'][0])

        if enemy_dir == move and (cond1 or cond2):
            self.logger.debug("Enemy running away from me.")
            return True
        return False

    def running_towards(self, move):
        if (not 'last_pos' in self.pursuing_enemy 
                or self.pursuing_enemy['last_pos'] is None 
                or self.pursuing_enemy is None):
            return False
        # self.logger.debug(str(self.pursuing_enemy))
        if (self.find_direction(
            self.pursuing_enemy['last_pos'], 
            self.pursuing_enemy['pos']
            ) == self.opposite_move(move)
                and ((self.cur_pos[0] == self.pursuing_enemy['pos'][0]) 
                    or (self.cur_pos[1] == self.pursuing_enemy['pos'][1]))):
            self.logger.debug("Enemy running towards me.")
            return True
        return False

    def select_bomb_point(self, target, i=0):
        closest = None
        for pos in [self.search_domain.result(target, mov) 
                for mov in self.search_domain.actions(target)]:
            if pos in self.walls:
                continue
            d = self.dist(self.cur_pos, pos)
            if closest is None or d < closest[1]:
                closest = (pos, d)

        if closest is None: # did not find place to put bomb
            self.logger.debug(f'Current wall {target} is blocked')
            target = self.closest_wall(i=i+1)
            return self.select_bomb_point(target, i+1)

        self.logger.debug("Closest wall: " + str(target) + 
                ". Going to " + str(closest[0]))
        
        self.bomb_point = closest[0]

        path, moves = self.calculate_path(self.cur_pos, closest[0])
        return (path, moves)
    
    

    def hide(self, path, moves):
        # hide in nearby position 
        # but choose the one closest to next wall ? not yet
        
        quad1 = [['w', 'd'],['d', 'w'],['w', 'w', 'd'],['d', 'd', 'w'],['w', 'w', 'w', 'd'],['d', 'd', 'd', 'w']]
        quad2 = [['w', 'a'],['a', 'w'],['w', 'w', 'a'],['a', 'a', 'w'],['a', 'a', 'a', 'w'],['w', 'w', 'w', 'a']]
        quad3 = [['s', 'a'],['a', 's'],['s', 's', 'a'],['a', 'a', 's'],['a', 'a', 'a', 's'],['s', 's', 's', 'a']]
        quad4 = [['s', 'd'],['d', 's'],['s', 's', 'd'],['d', 'd', 's'],['s', 's', 's', 'd'],['d', 'd', 'd', 's']]


        last_pos = path[-1]
        #Instead of none, we have a possibility to stay in place if there is no exit
        best = last_pos,['']


        quad1n = 0
        quad2n = 0
        quad3n = 0
        quad4n = 0

        for e in self.enemies:
            epos = e['pos']
            if self.search_domain.dist(last_pos, epos) < 8: #only the closests
                
                if last_pos[0] > epos[0]:   #esquerda
                    if last_pos[1] < epos[1]:    #baixo
                        quad3n += 2
                    if last_pos[1] > epos[1]:    #cima
                        quad2n += 2
                    else:
                        quad2n += 1
                        quad3n += 1

                if last_pos[0] < epos[0]:    #direita
                    if last_pos[1] < epos[1]:    #baixo
                        quad4n += 2
                    if last_pos[1] > epos[1]:    #cima
                        quad1n += 2
                    else:
                        quad1n += 1
                        quad4n += 1
        
        possible_moves = []

        if quad1n != 0 and quad2n==0 and quad3n==0 and quad4n==0:
            possible_moves += quad3 + quad4 + quad2 + quad1
        if quad1n == 0 and quad2n!=0 and quad3n==0 and quad4n==0:
            possible_moves += quad4 + quad1 + quad3 + quad2
        if quad1n == 0 and quad2n==0 and quad3n!=0 and quad4n==0:
            possible_moves += quad1 + quad2 + quad4 + quad3
        if quad1n == 0 and quad2n==0 and quad3n==0 and quad4n!=0:
            possible_moves += quad2 + quad3 + quad1 + quad4
        else:
            helper = {'quad1':quad1n,'quad2':quad2n,'quad3':quad3n,'quad4':quad4n}
            for i in sorted(helper.items(), key= lambda e : (e[1], e[0])):
                if i[0] == 'quad1':
                    possible_moves += quad1
                elif i[0] == 'quad2':
                    possible_moves += quad2
                elif i[0] == 'quad3':
                    possible_moves += quad3
                elif i[0] == 'quad4':
                    possible_moves += quad4


        for possible_move in possible_moves:

            p = [last_pos]
            this_works = True

            hide_path = self.result(possible_move)
            if len(self.enemies) > 0:
                for e in self.enemies:
                    if e['pos'] in hide_path:
                        this_works = False

            if not this_works:
                continue

            this_works = True
            
            #print(last_pos,possible_move)

            if self.can_i_do_this(last_pos, possible_move):
                for move in possible_move:
                    p.append(self.search_domain.result(p[-1], move))
                
                best = (p, possible_move)
                break
        #aqui verificar se best == None e se for talvez andar para tras conforme o radius da bomab?

        self.logger.debug("Hiding from bomb in " + str(best[0][-1]) + " (" + str(best[1]) + ")")

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
    
    def allBalloms(self):
        for e in self.enemies:
            if e['name'] not in ['Balloom', 'Doll']:
                return False
        return True
        
    def decide_move(self):
        if self.update_wallpass_next:
            self.logger.info("I can walk through walls now!")
            self.search_domain.wallpass = True
        if self.powerups: # powerup to pick up
            powerup_popped = self.powerups.pop(0) # 0 - pos, 1 - type
            powerup = powerup_popped[0]
            powerup_name = powerup_popped[1] # [[15, 16], 'Flames']
            self.have_powerup = True
            self.logger.debug("Going for powerup: " + str(powerup))
            path, moves = self.calculate_path(self.cur_pos, powerup)
            if len(self.enemies)>0:
                self.powerups.append(powerup)
                if str(powerup_name)=="Wallpass":
                    self.update_wallpass_next = True
                return [moves[0]]
            return moves

        if self.exit and not self.enemies and self.have_powerup:
            path, moves = self.calculate_path(self.cur_pos, self.exit)
            return moves
        
        #Does this solve?
        closest_enemy = self.closest_enemy()
        closest_wall = self.closest_wall()

        if (closest_enemy is not None 
            and (
                not self.walls
                or self.dist(self.cur_pos,closest_enemy['pos']) <= self.dist(self.cur_pos, closest_wall)
                #or (self.have_powerup and self.exit)
                )
            and not closest_enemy['pos'] in self.walls
           ):

            self.update_pursuing_enemy(closest_enemy)

            #se distancia for maior que o metade do tamanho do mapa, vamos para uma posiçao no meio e tentamos procurar a partir de la
            if False:
            #melhorar esta porcaria xd
            #if self.search_domain.dist(self.cur_pos, closest_enemy['pos']) >= self.map._size[1]/2:
                chosen_pos = [int(self.map._size[0]/2),int(self.map._size[1]/2)]
                self.logger.debug("Going for %s" %  (chosen_pos))
                while self.map.is_blocked(chosen_pos) or self.map.is_stone(chosen_pos) \
                    or chosen_pos not in self.search_domain.destroyed_walls or chosen_pos!=[self.map._size[0]-1,self.map._size[1]-1]:

                    chosen_pos = [ele + 1 for ele in chosen_pos]  
                    self.logger.debug("Going for %s" %  (chosen_pos))
                path, moves = self.calculate_path(self.cur_pos, chosen_pos)
                return moves

            else:
                path, moves = self.calculate_path(self.cur_pos, closest_enemy['pos'])
                if (len(moves) > 0 and self.search_domain.dist(self.cur_pos, closest_enemy['pos']) <= 2
                    and not self.running_away(moves[-1])):

                    if self.walls == [] and self.allBalloms():
                        self.perform_last_resort = True

                    moves = ['B']
                    self.incr_round()
                    self.hide([self.cur_pos], moves)
                elif self.search_domain.dist(self.cur_pos, closest_enemy['pos']) <= 1:
                    if self.walls == [] and self.allBalloms():
                        self.perform_last_resort = True

                    moves = ['B']
                    self.incr_round()
                    self.hide([self.cur_pos], moves)
                elif ((self.pursuing_enemy['name'] == 'Balloom' or self.pursuing_enemy['name'] == 'Doll') 
                    and self.pursuing_enemy['rounds_pursuing'] >= self.rounds_pursuing_limit):
       
                    enemy_direction = self.find_direction(self.pursuing_enemy['last_pos'], self.pursuing_enemy['pos'])
                    if enemy_direction is None:
                        enemy_direction = self.last_enemy_dir
                    if enemy_direction == 'w':
                        self.last_enemy_dir = 'w'
                        if not self.map.is_stone((self.cur_pos[0]-1, self.cur_pos[1])):
                            return ['a']
                        elif not self.map.is_stone((self.cur_pos[0], self.cur_pos[1]-1)):
                            return ['w']
                        else:
                            self.pursuing_enemy['rounds_pursuing'] = 0
                            return [moves[0]]
                    elif enemy_direction == 'a':
                        self.last_enemy_dir = 'a'
                        if not self.map.is_stone((self.cur_pos[0], self.cur_pos[1]+1)):
                            return ['s']
                        elif not self.map.is_stone((self.cur_pos[0]-1, self.cur_pos[1])):
                            return ['a']
                        else:
                            self.pursuing_enemy['rounds_pursuing'] = 0
                            return [moves[0]]

                    elif enemy_direction == 's':
                        self.last_enemy_dir = 's'
                        if not self.map.is_stone((self.cur_pos[0]+1, self.cur_pos[1])):
                            return ['d']
                        elif not self.map.is_stone((self.cur_pos[0], self.cur_pos[1]+1)):
                            return ['s']
                        else:
                            self.pursuing_enemy['rounds_pursuing'] = 0
                            return [moves[0]]

                    elif enemy_direction == 'd':
                        self.last_enemy_dir = 'd'
                        if not self.map.is_stone((self.cur_pos[0], self.cur_pos[1]-1)):
                            return ['w']
                        elif not self.map.is_stone((self.cur_pos[0]+1, self.cur_pos[1])):
                            return ['d']
                        else:
                            self.pursuing_enemy['rounds_pursuing'] = 0
                            return [moves[0]]
                
                elif self.perform_last_resort:
                    '''pos = [1,1]
                    while self.map.is_blocked(pos) or self.map.is_stone(pos):
                        pos = [x+1 for x in pos] 
                    if self.cur_pos == pos:
                        return ''
                    self.logger.info("Chosen position to camp: %s" % (pos))
                    path, moves = self.calculate_path(self.cur_pos, pos)
                    return [moves[0]]'''
                    if not self.map.is_stone((self.cur_pos[0], self.cur_pos[1]-1)):
                        return ['w']
                    elif not self.map.is_stone((self.cur_pos[0]-1, self.cur_pos[1])):
                        return ['a']
                    else:
                        return ['']
                
                elif self.pursuing_enemy['name'] in ['Oneal','Minvo','Ovapi', 'Kondoria', 'Pass'] and self.pursuing_enemy['rounds_pursuing'] > 10:
                    self.pursuing_enemy['rounds_pursuing'] = 0
                    if self.cur_pos[0] > self.pursuing_enemy['pos'][0]:
                        return ['a','s','a','s','a']
                    else:
                        return ['d','s','d','s','d']
                else:
                    return [moves[0]]

        elif closest_wall != None:
            # self.eval_enemy = False
            path, moves = self.select_bomb_point(closest_wall) 
            if not self.enemies or self.search_domain.dist(self.cur_pos, closest_wall) <= 1:
                moves.append('B') # leave a bomb at the end
                self.hide(path, moves)
            else:
                return [moves[0]]

        if (self.level == 3 and self.have_powerup or self.level > 3):
            moves.append('A')
        return moves

    def next_move(self, state):

        if self.enemies != None and len(self.enemies) != len(state['enemies']):  #Enemy killed
            self.perform_last_resort = False

        self.cur_pos = state['bomberman']
        self.enemies = state['enemies']
        self.powerups = state['powerups']
        self.bonus = state['bonus']
        self.exit = state['exit']
        #self.walls = state['walls']

        ##Keep track of enemies past positions to check for loops
        #for enemy in self.enemies:
        #    if enemy['id'] in self.enemy_past_pos:
        #        old_pos = self.enemy_past_pos[enemy['id']]
        #        new_pos = enemy['pos']
        #        old_pos.append(new_pos)
        #        self.enemy_past_pos[enemy['id']] = old_pos
            # else:
            #     self.enemy_past_pos[enemy['id']] = [enemy['pos']] 

        # self.logger.info("Past enemies positions: %s" % (self.enemy_past_pos))
        # Workaround to compare previous and current walls
        new_walls = state['walls']
        if self.walls is not None:
            for wall in [w for w in self.walls if w not in new_walls]:
                self.search_domain.set_destroyed_wall(wall)
        self.walls = new_walls

        lost_life = self.lives != state['lives']
        self.lives = state['lives']

        #Clear after death
        if lost_life:
            self.reset_life()

        level = state['level']
        self.update_level(level)

        # if queue is empty and there are no bombs placed
        if ((not self.decisions_queue) and not state['bombs']):
            self.decisions_queue = self.decide_move()

        if not self.decisions_queue:
            return ['']

        self.logger.debug("Path: " + str(self.decisions_queue))
        next_move = self.decisions_queue.pop(0)
        self.logger.debug("Next move: " + str(next_move))

        return next_move

class BombermanSearch(SearchDomain):

    # construtor
    def __init__(self, map, destroyed_walls=[]):
        self.map = map
        self.logger = logging.getLogger("AI AGENT")
        self.logger.setLevel(logging.WARN)
        self.destroyed_walls = []
        self.wallpass = False

    #Alterar para isto
    def set_destroyed_wall(self, destroyed_wall):
        # print(f"Detroyed Wall: {destroyed_wall}")
        #self.map.remove_wall(destroyed_wall)
        self.destroyed_walls.append(destroyed_wall)

    def remove_destroyed_walls(self):
        self.destroyed_walls = []

    def set_walls(self, walls):
        self.map.walls = walls

    # lista de accoes possiveis num estado
    def actions(self, state):
        pos = state
        moves = ['w', 'a', 's', 'd']
        actions_list = []
        
        for move in moves:
            next_pos = self.result(pos, move)
            if (((not self.map.is_blocked(next_pos) or self.wallpass) and 
                    not self.map.is_stone(next_pos)) or next_pos in self.destroyed_walls):
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
    def cost(self, state, action, enemy=False):
        # if enemy:
        #     return 20
        return 1

    def dist(self, pos1, pos2):
        # return math.hypot(pos2[0]-pos1[0],pos2[1]-pos1[1])
        return abs(pos2[0]-pos1[0]) + abs(pos2[1]-pos1[1])

    # custo estimado de chegar de um estado a outro
    def heuristic(self, state, goal_state):
        return self.dist(state, goal_state)

