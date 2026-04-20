from typing import Any, Generic, TypeVar

from bnbpy.cython.manager import BaseNodeManager
from bnbpy.cython.node import Node
from bnbpy.cython.problem import Problem

P = TypeVar('P', bound=Problem)

class PriEntry(Generic[P]):
    node: Node[P]
    priority: Any

    def __init__(self, node: Node[P], priority: Any) -> None: ...
    def __lt__(self, other: 'PriEntry[P]') -> bool: ...
    def get_priority(self) -> Any: ...

class PriorityQueue(BaseNodeManager[P]):
    """
    Class for managing active nodes in Branch & Bound algorithm
    using a priority queue.

    Note that due to Cython limitations this class is not implemented as
    an ABC class, but it is mandatory to implement the following methods
    in subclasses:

    *   `not_empty`
    *   `enqueue`
    *   `dequeue`
    *   `get_lower_bound`
    *   `pop_lower_bound`
    *   `clear`
    """

    heap: list[PriEntry[P]]

    def size(self) -> int: ...
    def not_empty(self) -> bool: ...
    def enqueue(self, node: Node[P]) -> None: ...
    def enqueue_all(self, nodes: list[Node[P]]) -> None: ...
    def dequeue(self) -> Node[P] | None: ...
    def get_lower_bound(self) -> Node[P] | None: ...
    def pop_lower_bound(self) -> Node[P] | None: ...
    def clear(self) -> None: ...
    def filter_by_lb(self, max_lb: float) -> None: ...
    def pop_all(self) -> list[Node[P]]: ...
    def get_heap(self) -> list[PriEntry[P]]: ...
    def make_entry(self, node: Node[P]) -> PriEntry[P]:
        """Return a :class:`PriEntry` for *node*.

        Subclasses must override this to define the ordering key.

        Parameters
        ----------
        node : Node[P]
            Node to wrap.

        Returns
        -------
        PriEntry[P]
            Heap entry carrying *node* and its ordering priority.
        """
        ...

class DfsPriQueue(PriorityQueue[P]):
    """
    Depth-First Search priority queue implementation with
    tie-breaking by lower bound and node index (greater first).
    """

    def make_entry(self, node: Node[P]) -> PriEntry[P]: ...

class BfsPriQueue(PriorityQueue[P]):
    """
    Breadth-First Search priority queue implementation with
    tie-breaking by lower bound and node index (smaller first).
    """

    def make_entry(self, node: Node[P]) -> PriEntry[P]: ...

class BestPriQueue(PriorityQueue[P]):
    """
    Best-First Search priority queue implementation.

    Nodes are ordered by lower bound, with tie-breaking by tree level
    (deeper nodes first) and node index (greater first).
    """

    def make_entry(self, node: Node[P]) -> PriEntry[P]: ...
    def get_lower_bound(self) -> Node[P] | None: ...
    def pop_lower_bound(self) -> Node[P] | None: ...
