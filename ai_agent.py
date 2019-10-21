
import json
import logging
import math

from mapa import Map

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

class AI_Agent():

    def __init__(self, game_properties):
        self.logger = logging.getLogger("AI AGENT")
        self.logger.setLevel(logging.DEBUG)
        self.logger.info("AI Agent created.")
        self.map = Map(size=game_properties["size"], mapa=game_properties["map"])
        self.logger.info(self.map)

    def dist(self, pos1, pos2):
        return math.hypot(pos2[0]-pos1[0],pos2[1]-pos1[1])

    def closest_enemy(self, cur_pos, enemies):
        closest = None
        for enemy in enemies:
            d = self.dist(cur_pos, enemy['pos'])
            if closest is None or d < closest[1]:
                closest = (enemy, d)
        return closest[0] 

    def next_move(self, state):
        # self.logger.info(state)
        cur_pos = state['bomberman']
        enemies = state['enemies']
        des_walls = state['walls']

        if len(enemies) > 0:
            # go for enemy
            c = self.closest_enemy(cur_pos, enemies)
            self.logger.info("Going for enemy: " + str(c))
            return c

        return state


# Example output of STATE 

# 2019-10-19 16:40:12,026 - AI AGENT - INFO - {'level': 1, 'step': 55, 'timeout': 3000, 'player': 'jota', 'score': 0, 'lives': 2, 'bomberman': [1, 1], 'bombs': [], 'enemies': [{'name': 'Balloom', 'id': '1a0fb382-61e5-412b-a875-9b2f950f55d5', 'pos': [6, 1]}, {'name': 'Balloom', 'id': '7652ed24-1dd7-4105-bcfd-711318ebf3c0', 'pos': [10, 1]}, {'name': 'Balloom', 'id': '460230f7-6866-4706-8c78-d4cdd10030a7', 'pos': [10, 23]}, {'name': 'Balloom', 'id': '8c508ccd-eba0-4930-a5ea-c4313151015e', 'pos': [11, 23]}, {'name': 'Balloom', 'id': '44526b3b-02c8-4b1e-8245-e29f4e383f13', 'pos': [19, 22]}, {'name': 'Balloom', 'id': 'deda45d7-1d20-45d8-b39d-3e62365072e2', 'pos': [1, 22]}], 'walls': [[3, 11], [3, 24], [3, 29], [4, 3], [5, 26], [6, 21], [7, 23], [10, 11], [10, 27], [11, 4], [11, 7], [12, 21], [12, 25], [13, 7], [13, 29], [14, 15], [15, 4], [17, 18], [17, 20], [19, 11], [21, 17], [21, 28], [23, 3], [24, 7], [24, 25], [25, 3], [25, 5], [25, 20], [26, 9], [27, 15], [27, 19], [28, 15], [29, 10], [29, 28], [30, 17], [30, 19], [35, 6], [35, 14], [35, 19], [35, 20], [35, 23], [36, 15], [37, 12], [38, 7], [39, 11], [39, 27], [40, 9], [40, 13], [41, 4], [41, 25], [45, 12], [46, 17], [46, 29], [48, 11], [48, 17]], 'powerups': [], 'bonus': [], 'exit': []}

