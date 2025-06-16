from typing import (
    Any,
    Generic,
    Optional,
    Type,
    TypeVar,
)

T = TypeVar('T', bound='BaseNode[Any]')


class BaseNode(Generic[T]):
    index: int
    neighbors: set[T]
    degree: int

    def __init__(self, index: int, neighbors: Optional[set[T]] = None):
        self.index = index
        if neighbors is None:
            neighbors = set()
        self.neighbors = neighbors
        self.degree = len(self.neighbors)

    def __repr__(self) -> str:
        return f'N({self.index})'

    def add_neighbor(self, neighbor: T) -> None:
        self.neighbors.add(neighbor)
        neighbor.neighbors.add(self)
        self._update_degree()
        neighbor._update_degree()

    def remove_neighbor(self, neighbor: T) -> None:
        if neighbor in self.neighbors:
            self.neighbors.remove(neighbor)
        if self in neighbor.neighbors:
            neighbor.neighbors.remove(self)
        self._update_degree()
        neighbor._update_degree()

    def _update_degree(self) -> None:
        self.degree = len(self.neighbors)


class BaseGraph(Generic[T]):
    nodes: dict[int, T]
    _node_cls: Type[T]

    def __init__(self, edges: list[tuple[int, int]]):
        self.nodes = {}
        for i, j in edges:
            n_i = self.get_node(i)
            n_j = self.get_node(j)
            n_i.add_neighbor(n_j)

    def get_node(self, i: int) -> T:
        if i in self.nodes:
            return self.nodes[i]
        self.nodes[i] = self._node_cls(i)
        return self.nodes[i]

    def _set_node_cls(self, node_cls: Type[T]) -> None:
        self._node_cls = node_cls
