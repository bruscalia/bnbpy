import random
from functools import total_ordering
from typing import Dict, List, Optional, Set, Tuple, Type, Union

from bnbprob.gcol.base import BaseGraph, BaseNode


class IndepSetNode(BaseNode):
    neighbors: Set['IndepSetNode']
    selected: bool
    weight: float
    degree_red: int
    active_degree: int

    def __init__(
        self,
        index,
        neighbors: Optional[Set['IndepSetNode']] = None,
        weight: float = 1.0,
    ):
        super().__init__(index, neighbors)
        self.weight = weight
        self.selected = False
        self.degree_red = 0
        self.active_degree = self.degree - self.degree_red

    def select(self):
        self.selected = True
        for n in self.neighbors:
            n.degree_red += 1
            n.active_degree = n.degree - n.degree_red


class IndepGraph(BaseGraph):
    nodes: Dict[int, IndepSetNode]

    def __init__(
        self, edges: List[Tuple[int]], cls: Type[IndepSetNode] = IndepSetNode
    ):
        super().__init__(edges, cls)

    def set_weights(self, weights: List[float]):
        for j, w in enumerate(weights):
            self.nodes[j].weight = w

    def clean(self):
        for node in self.nodes.values():
            node.selected = False
            node.degree = len(node.neighbors)
            node.degree_red = 0
            node.active_degree = node.degree


@total_ordering
class IndepSetSolution:
    cost: Union[float, int]
    nodes: Set[IndepSetNode]

    def __init__(self, nodes: Optional[Set[IndepSetNode]] = None):
        if nodes is None:
            nodes = set()
        self.nodes = nodes
        self.cost = sum(n.weight for n in self.nodes)

    def add(self, node: 'IndepSetNode'):
        self.nodes.add(node)
        self.cost += node.weight

    def __hash__(self):
        return hash(str(self.nodes))

    def __len__(self):
        return len(self.nodes)

    def __eq__(self, other):
        if not isinstance(other, IndepSetSolution):
            return NotImplemented
        return self.cost == other.cost

    def __lt__(self, other):
        if not isinstance(other, IndepSetSolution):
            return NotImplemented
        return self.cost < other.cost

    def __repr__(self):
        return f"IndepSetSolution({self.cost})"


class IndepSetHeur:
    graph: Optional[IndepGraph]
    sol: Set[IndepSetNode]
    history: List['IndepSetNode']

    def __init__(self) -> None:
        self.graph = None
        self.sol = IndepSetSolution()
        self.history = []

    def solve(self, graph: IndepGraph, save_history=False) -> IndepSetSolution:
        self.sol = IndepSetSolution()
        self.graph = graph
        self.graph.clean()
        self.history = []
        self.queue = list(self.graph.nodes.values())  # Pool of uncolored nodes
        for i in range(len(self.queue)):
            node = self.dequeue()
            self.select(node)
            if save_history:
                self.history.append(node)
            if len(self.queue) == 0:
                assert len(self.sol) == i + 1, 'Problems in indep set size'
                break
        return self.sol

    def select(self, node: IndepSetNode):
        node.select()
        self.sol.add(node)
        for other in node.neighbors:
            if other in self.queue:
                self.queue.remove(other)

    def dequeue(self) -> IndepSetNode:
        node = max(self.queue, key=lambda x: x.weight / x.active_degree)
        self.queue.remove(node)
        return node


class RandomIndepSet(IndepSetHeur):
    def __init__(self, seed=None):
        super().__init__()
        self.rng = random.Random(seed)

    def dequeue(self):
        node = self.rng.choice(self.queue)
        self.queue.remove(node)
        return node


class TargetMultiStart(RandomIndepSet):
    greedy: IndepSetHeur
    target: Union[float, int]
    base_iter: int
    max_iter: int

    def __init__(self, seed=None, target=1.0, base_iter=10, max_iter=100):
        """Random selection heuristic with stoppage based on target value.

        Parameters
        ----------
        seed : int, optional
            Seed for random generator, by default None

        target : float, optional
            Target value, by default 1.0

        base_iter : int, optional
            Base number of iterations, by default 10

        max_iter : int, optional
            Maximum number of iterations, by default 100
        """
        super().__init__(seed)
        self.greedy = IndepSetHeur()
        self.target = target
        self.base_iter = base_iter
        self.max_iter = max_iter

    def solve(self, graph: IndepGraph):
        best_sol = self.greedy.solve(graph)
        if best_sol.cost >= self.target:
            return best_sol
        for i in range(self.max_iter):
            sol = super().solve(graph)
            if sol.cost > best_sol.cost:
                best_sol = sol
            if best_sol.cost >= self.target and i >= self.base_iter:
                return self._prepare_return(graph, best_sol)
        return self._prepare_return(graph, best_sol)

    def _prepare_return(self, graph: IndepGraph, sol: IndepSetSolution):
        graph.clean()
        for node in sol.nodes:
            self.select(node)
        self.sol = sol
        return self.sol
