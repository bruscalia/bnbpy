import random
from typing import Dict, List, Optional, Set, Tuple, Type

from bnbprob.gcol.base import BaseGraph, BaseNode


class Color:
    index: int
    nodes: Set['ColorNode']

    def __init__(self, index, nodes=None) -> None:
        self.index = index
        if nodes is None:
            nodes = set()
        self.nodes = nodes

    def __repr__(self):
        return f'C({self.index})'

    @property
    def size(self):
        return len(self.nodes)

    def add_node(self, node: 'ColorNode'):
        self.nodes.add(node)

    def clean_nodes(self):
        for n in self.nodes:
            n.color = None


class ColorNode(BaseNode):
    color: Color
    neighbors: Set['ColorNode']

    def __init__(
        self,
        index,
        neighbors: Optional[Set['ColorNode']] = None,
        color: Optional['Color'] = None,
    ):
        super().__init__(index, neighbors=neighbors)
        self.color = color

    def __repr__(self) -> str:
        return f'N({self.index})|{self.color}'

    def set_color(self, color: Color):
        self.color = color
        color.add_node(self)

    @property
    def active(self):
        return self.color is not None

    @property
    def neighbor_colors(self):
        return {n.color for n in self.neighbors if n.active}

    @property
    def saturation(self):
        return len(self.neighbor_colors)


class ColorGraph(BaseGraph):
    nodes: Dict[int, 'ColorNode']
    colors: List[Color]

    def __init__(
        self, edges: List[Tuple[int]], cls: Type[ColorNode] = ColorNode
    ):
        super().__init__(edges, cls)
        self.colors = []

    def add_color(self):
        color = Color(len(self.colors))
        self.colors.append(color)
        return color

    @property
    def size(self):
        return len(self.nodes)

    def clean(self):
        for c in self.colors:
            c.clean_nodes()
        self.colors = []


class ColorHeuristic:
    graph: Optional[ColorGraph]
    history: List['ColorNode']

    def __init__(self):
        self.graph = None
        self.history = []
        self.queue = []

    def find_next_color(self, node: ColorNode) -> Color:
        neighbor_colors = node.neighbor_colors
        for c in self.graph.colors:
            if c not in neighbor_colors:
                return c
        return self.graph.add_color()

    def solve(self, graph: ColorGraph, save_history=False):
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

    def dequeue(self):
        node = max(self.queue, key=lambda x: (x.saturation, x.degree))
        self.queue.remove(node)
        return node

    @property
    def cost(self):
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

    def __init__(self, seed=None):
        super().__init__()
        self.rng = random.Random(seed)

    def dequeue(self):
        node = self.rng.choice(self.queue)
        self.queue.remove(node)
        return node
