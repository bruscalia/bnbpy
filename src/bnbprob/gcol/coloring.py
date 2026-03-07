import random
from typing import List, Optional

from bnbprob.gcol.base import BaseGraph, BaseNode


class Color:
    index: int
    nodes: set['ColorNode']

    def __init__(self, index: int, nodes: Optional[set['ColorNode']] = None):
        self.index = index
        if nodes is None:
            nodes = set()
        self.nodes = nodes

    def __repr__(self) -> str:
        return f'C({self.index})'

    @property
    def size(self) -> int:
        return len(self.nodes)

    def add_node(self, node: 'ColorNode') -> None:
        self.nodes.add(node)

    def clean_nodes(self) -> None:
        for n in self.nodes:
            n.color = None


class ColorNode(BaseNode['ColorNode']):
    color: Color | None
    neighbors: set['ColorNode']

    def __init__(
        self,
        index: int,
        neighbors: Optional[set['ColorNode']] = None,
        color: Optional['Color'] = None,
    ):
        super().__init__(index, neighbors=neighbors)
        self.color = color

    def __repr__(self) -> str:
        return f'N({self.index})|{self.color}'

    def set_color(self, color: Color) -> None:
        self.color = color
        color.add_node(self)

    @property
    def active(self) -> bool:
        return self.color is not None

    @property
    def neighbor_colors(self) -> set[Color]:
        return {
            n.color for n in self.neighbors if n.active and n.color is not None
        }

    @property
    def saturation(self) -> int:
        return len(self.neighbor_colors)


class ColorGraph(BaseGraph[ColorNode]):
    colors: List[Color]

    def __init__(self, edges: list[tuple[int, int]]):
        self._set_node_cls(ColorNode)
        super().__init__(edges)
        self.colors = []

    def add_color(self) -> Color:
        color = Color(len(self.colors))
        self.colors.append(color)
        return color

    @property
    def size(self) -> int:
        return len(self.nodes)

    def clean(self) -> None:
        for c in self.colors:
            c.clean_nodes()
        self.colors = []


class ColorHeuristic:
    graph: Optional[ColorGraph]
    history: List['ColorNode']
    queue: List['ColorNode']

    def __init__(self) -> None:
        self.graph = None
        self.history = []
        self.queue = []

    def find_next_color(self, node: ColorNode) -> Color:
        neighbor_colors = node.neighbor_colors
        if self.graph is None:
            raise ValueError("Graph is not set. Call 'solve' method first.")
        for c in self.graph.colors:
            if c not in neighbor_colors:
                return c
        return self.graph.add_color()

    def solve(self, graph: ColorGraph, save_history: bool = False) -> None:
        self.graph = graph
        self.graph.clean()
        self.history = []
        self.queue = list(self.graph.nodes.values())  # Pool of uncolored nodes
        while len(self.queue) > 0:
            node = self.dequeue()
            color = self.find_next_color(node)
            node.set_color(color)
            if save_history:
                self.history.append(node)
        self.graph.colors.sort(key=lambda x: len(x.nodes), reverse=True)

    def dequeue(self) -> ColorNode:
        node = max(self.queue, key=lambda x: (x.saturation, x.degree))
        self.queue.remove(node)
        return node

    @property
    def cost(self) -> int:
        if self.graph is None:
            return 0
        return len(self.graph.colors)


class DSatur(ColorHeuristic):
    """
    Graph Coloring DSatur Algorithm proposed by Brélaz (1979)

    Brélaz, D., 1979. New methods to color the vertices of a graph.
    Communications of the ACM, 22(4), 251-256.
    """

    # Just an alias
    pass


class RandomColoring(ColorHeuristic):
    def __init__(self, seed: Optional[int] = None) -> None:
        super().__init__()
        self.rng = random.Random(seed)

    def dequeue(self) -> ColorNode:
        node = self.rng.choice(self.queue)
        self.queue.remove(node)
        return node
