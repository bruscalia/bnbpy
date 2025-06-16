import random
from functools import total_ordering
from logging import getLogger
from typing import Dict, Optional, Union

from bnbprob.gcol.base import BaseGraph, BaseNode

log = getLogger(__name__)


class IndepSetNode(BaseNode['IndepSetNode']):
    neighbors: set['IndepSetNode']
    selected: bool
    weight: float
    degree_red: int
    active_degree: int

    def __init__(
        self,
        index: int,
        neighbors: Optional[set['IndepSetNode']] = None,
        weight: float = 1.0,
    ):
        super().__init__(index, neighbors)
        self.weight = weight
        self.selected = False
        self.degree_red = 0
        self.active_degree = self.degree - self.degree_red

    def select(self) -> None:
        self.selected = True
        for n in self.neighbors:
            n.degree_red += 1
            n.active_degree = n.degree - n.degree_red


class IndepGraph(BaseGraph['IndepSetNode']):
    nodes: Dict[int, IndepSetNode]

    def __init__(self, edges: list[tuple[int, int]]):
        self._set_node_cls(IndepSetNode)
        super().__init__(edges)

    def set_weights(self, weights: list[float]) -> None:
        for j, w in enumerate(weights):
            self.nodes[j].weight = w

    def clean(self) -> None:
        for node in self.nodes.values():
            node.selected = False
            node.degree = len(node.neighbors)
            node.degree_red = 0
            node.active_degree = node.degree


@total_ordering
class IndepSetSolution:
    cost: Union[float, int]
    nodes: set[IndepSetNode]

    def __init__(self, nodes: Optional[set[IndepSetNode]] = None):
        if nodes is None:
            nodes = set()
        self.nodes = nodes
        self.cost = sum(n.weight for n in self.nodes)

    def add(self, node: 'IndepSetNode') -> None:
        self.nodes.add(node)
        self.cost += node.weight

    def __hash__(self) -> int:
        return hash(str(self.nodes))

    def __len__(self) -> int:
        return len(self.nodes)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, IndepSetSolution):
            raise NotImplementedError(
                f'Cannot compare {type(self)} with {type(other)}'
            )
        return self.cost == other.cost

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, IndepSetSolution):
            raise NotImplementedError(
                f'Cannot compare {type(self)} with {type(other)}'
            )
        return self.cost < other.cost

    def __repr__(self) -> str:
        return f'IndepSetSolution({self.cost})'


class IndepSetHeur:
    graph: Optional[IndepGraph]
    sol: IndepSetSolution
    queue: list['IndepSetNode']
    history: list['IndepSetNode']

    def __init__(self) -> None:
        self.graph = None
        self.sol = IndepSetSolution()
        self.history = []

    def solve(
        self, graph: IndepGraph, save_history: bool = False
    ) -> IndepSetSolution:
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

    def select(self, node: IndepSetNode) -> None:
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
    def __init__(self, seed: Optional[int] = None):
        super().__init__()
        self.rng = random.Random(seed)

    def dequeue(self) -> IndepSetNode:
        node = self.rng.choice(self.queue)
        self.queue.remove(node)
        return node


class TargetMultiStart(RandomIndepSet):
    greedy: IndepSetHeur
    target: Union[float, int]
    base_iter: int
    max_iter: int

    def __init__(
        self,
        seed: Optional[int] = None,
        target: Union[float, int] = 1.0,
        base_iter: int = 10,
        max_iter: int = 100,
    ):
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

    def solve(
        self, graph: IndepGraph, save_history: bool = False
    ) -> IndepSetSolution:
        if save_history:
            log.warning(
                'TargetMultiStart does not support saving history, '
                'history will not be saved.'
            )
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

    def _prepare_return(
        self, graph: IndepGraph, sol: IndepSetSolution
    ) -> IndepSetSolution:
        graph.clean()
        for node in sol.nodes:
            self.select(node)
        self.sol = sol
        return self.sol
