from typing import Dict, List, Optional, Set, Tuple, Type


class BaseNode:
    index: int
    neighbors: Set['BaseNode']
    degree = int

    def __init__(self, index, neighbors: Optional[Set['BaseNode']] = None):
        self.index = index
        if neighbors is None:
            neighbors = set()
        self.neighbors = neighbors
        self.degree = len(self.neighbors)

    def __repr__(self) -> str:
        return f'N({self.index})'

    def add_neighbor(self, neighbor: 'BaseNode'):
        self.neighbors.add(neighbor)
        neighbor.neighbors.add(self)
        self._update_degree()
        neighbor._update_degree()

    def remove_neighbor(self, neighbor: 'BaseNode'):
        if neighbor in self.neighbors:
            self.neighbors.remove(neighbor)
        if self in neighbor.neighbors:
            neighbor.neighbors.remove(self)
        self._update_degree()
        neighbor._update_degree()

    def _update_degree(self):
        self.degree = len(self.neighbors)


class BaseGraph:
    nodes: Dict[int, 'BaseNode']

    def __init__(
        self, edges: List[Tuple[int, int]], cls: Type[BaseNode] = BaseNode
    ):
        self.nodes = {}
        for i, j in edges:
            n_i = self.get_node(i, cls=cls)
            n_j = self.get_node(j, cls=cls)
            n_i.add_neighbor(n_j)

    def get_node(self, i: int, cls: Type[BaseNode] = BaseNode) -> BaseNode:
        if i in self.nodes:
            return self.nodes[i]
        self.nodes[i] = cls(i)
        return self.nodes[i]
