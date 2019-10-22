

# Modulo: tree_search
# 
# Fornece um conjunto de classes para suporte a resolucao de 
# problemas por pesquisa em arvore:
#    SearchDomain  - dominios de problemas
#    SearchProblem - problemas concretos a resolver 
#    SearchNode    - nos da arvore de pesquisa
#    SearchTree    - arvore de pesquisa, com metodos para 
#                    a respectiva construcao
#
#  (c) Luis Seabra Lopes
#  Introducao a Inteligencia Artificial, 2012-2018,
#  Inteligência Artificial, 2014-2018

from abc import ABC, abstractmethod

# Dominios de pesquisa
# Permitem calcular
# as accoes possiveis em cada estado, etc
class SearchDomain(ABC):

    # construtor
    @abstractmethod
    def __init__(self):
        pass

    # lista de accoes possiveis num estado
    @abstractmethod
    def actions(self, state):
        pass

    # resultado de uma accao num estado, ou seja, o estado seguinte
    @abstractmethod
    def result(self, state, action):
        pass

    # custo de uma accao num estado
    @abstractmethod
    def cost(self, state, action):
        pass

    # custo estimado de chegar de um estado a outro
    @abstractmethod
    def heuristic(self, state, goal_state):
        pass

# Problemas concretos a resolver
# dentro de um determinado dominio
class SearchProblem:
    def __init__(self, domain, initial, goal):
        self.domain = domain
        self.initial = initial
        self.goal = goal
    def goal_test(self, state):
        return state == self.goal

# Nos de uma arvore de pesquisa
class SearchNode:

    def __init__(self, state, parent=None, depth=0, cum_cost=0, heuristic=0): 
        self.state = state
        self.parent = parent
        self.depth = depth
        self.cum_cost = cum_cost
        self.heuristic = heuristic

    # verifica de forma recursiva se node esta no parent
    def in_parent(self, state):
        if self.parent is None:
            return self.state == state 
        return self.state == state or self.parent.in_parent(state)

    def __str__(self):
        # return f"no({self.state}, {self.parent}, {self.depth})"
        return f"node({self.state})"

    def __repr__(self):
        return str(self)

# Arvores de pesquisa
class SearchTree:

    # construtor
    def __init__(self, problem, strategy='breadth'): 
        self.problem = problem
        root = SearchNode(problem.initial, None, 0, 0, self.problem.domain.heuristic(self.problem.initial, self.problem.goal)) # depth and cum_cost initialized at 0
        self.open_nodes = [root]
        self.strategy = strategy
        self.length = 0
        self.cost = 0
        self.terminal_nodes = 0
        self.non_terminal_nodes = 1
        self.ramification = 0
        self.most_cum_cost = []
        self.depth_list = []
        self.avg_depth = 0

    # obter o caminho (sequencia de estados) da raiz ate um no
    def get_path(self,node):
        if node.parent == None:
            return [node.state]
        path = self.get_path(node.parent)
        path += [node.state]
        # path += [node]
        print(path)
        return (path)

    # obter o comprimento da soluçao
    def get_path_length(self, node):
        if node.parent is None:
            return 0
        return self.get_path_length(node.parent)+1

    # procurar a solucao
    def search(self, depth_limit):
        while self.open_nodes != []:
            node = self.open_nodes.pop(0)
            self.cost+=node.cum_cost
            self.length += 1
            self.depth_list.append(node.depth)

            if len(self.most_cum_cost) == 0 or node.cum_cost > self.most_cum_cost[0].cum_cost:
                self.most_cum_cost = [node]
            elif node.cum_cost == self.most_cum_cost[0].cum_cost and not node in self.most_cum_cost:
                self.most_cum_cost.append(node)

            if self.problem.goal_test(node.state):
                self.avg_depth = sum(self.depth_list) / len(self.depth_list)
                return self.get_path(node)
            lnewnodes = []
            node_actions = self.problem.domain.actions(node.state)
            for a in node_actions:
                newstate = self.problem.domain.result(node.state,a)
                if (not node.in_parent(newstate)) and node.depth < depth_limit:
                    lnewnodes += [SearchNode(newstate,
                                             node, 
                                             node.depth+1, 
                                             node.cum_cost + self.problem.domain.cost(node.state, a),
                                             self.problem.domain.heuristic(newstate, self.problem.goal)
                                            )]
            self.add_to_open(lnewnodes)
            if lnewnodes == []:
                self.terminal_nodes += 1
                self.non_terminal_nodes -= 1
            self.non_terminal_nodes += len(lnewnodes)
            self.ramification = self.length / self.non_terminal_nodes
        return None

    # juntar novos nos a lista de nos abertos de acordo com a estrategia
    def add_to_open(self,lnewnodes):
        if self.strategy == 'breadth':
            self.open_nodes.extend(lnewnodes)
        elif self.strategy == 'depth':
            self.open_nodes[:0] = lnewnodes
        elif self.strategy == 'uniform':
            self.open_nodes.extend(lnewnodes)
            self.open_nodes = sorted(self.open_nodes, key=lambda node: node.cum_cost)
        elif self.strategy == 'greedy':
            self.open_nodes = sorted(self.open_nodes + lnewnodes, key=lambda node: node.heuristic)
        elif self.strategy == 'a*':
            self.open_nodes = sorted(self.open_nodes + lnewnodes, key=lambda node: node.cum_cost + node.heuristic)

