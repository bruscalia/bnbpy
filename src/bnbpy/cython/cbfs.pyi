from typing import Generic, TypeVar

from bnbpy.cython.manager import BaseNodeManager
from bnbpy.cython.node import Node
from bnbpy.cython.priqueue_cpp import CppPriorityQueue
from bnbpy.cython.problem import Problem

P = TypeVar('P', bound=Problem)

class CycleLevel(Generic[P]):
    """A single level in a :class:`CycleQueue`.

    Internally holds a :class:`~bnbpy.cython.priqueue.PriorityQueue` for
    nodes at this level and maintains doubly-linked pointers to neighbouring
    levels.
    """

    level: int
    next: 'CycleLevel[P]'
    prev: 'CycleLevel[P]'

    def __init__(self, level: int) -> None: ...
    def size(self) -> int:
        """Return the number of nodes at this level."""
        ...

    def set_queue(self, pri_queue: CppPriorityQueue[P]) -> None:
        """Replace the internal priority queue.

        Parameters
        ----------
        pri_queue : PriorityQueue[P]
            New priority queue to use at this level.
        """
        ...

    def add_node(self, node: Node[P]) -> None:
        """Enqueue a node at this level.

        Parameters
        ----------
        node : Node[P]
            Node to add.
        """
        ...

    def pop_node(self) -> Node[P] | None:
        """Dequeue and return the next node at this level.

        Returns
        -------
        Node[P] | None
            Next node, or ``None`` if the level is empty.
        """
        ...

    def filter(self, max_lb: float) -> None:
        """Discard nodes whose ``lb >= max_lb``.

        Parameters
        ----------
        max_lb : float
            Upper-bound threshold (exclusive).
        """
        ...

class CycleQueue(BaseNodeManager[P]):
    """A cycling level-based node manager.
    Useful for cyclic best-first search implementations.

    Nodes are bucketed by tree level. The manager cycles through each level
    in round-robin order, always dequeuing the best node within the
    current level. When the number of stored nodes exceeds *max_size* the
    manager falls back to its ``fallback_queue``
    (by default a DFS priority queue)
    until the load drops to half of *max_size*.
    """

    levels: list[CycleLevel[P]]
    current_level: CycleLevel[P]
    start_level: CycleLevel[P]
    last_level: CycleLevel[P]
    node_counter: int
    max_size: int
    use_fallback: bool
    permanent_fallback: bool
    fallback_queue: CppPriorityQueue[P]

    def __init__(
        self,
        max_size: int = 100_000,
        permanent_fallback: bool = False,
    ) -> None:
        """Initialise the cycle queue.

        Parameters
        ----------
        max_size : int, optional
            Maximum number of nodes before switching to the fallback DFS
            queue, by default 100 000.

        permanent_fallback : bool, optional
            If ``True``, once the fallback queue is entered it will never be
            exited, even if the load drops below the threshold.
        """
        ...

    def new_level(self, level: int) -> CycleLevel[P]:
        """Create a new :class:`CycleLevel` for the given depth.

        Override in subclasses to customise the per-level priority queue.

        Parameters
        ----------
        level : int
            Tree depth of the new level.

        Returns
        -------
        CycleLevel[P]
            The newly created level.
        """
        ...

    def size(self) -> int: ...
    def not_empty(self) -> bool: ...
    def enqueue(self, node: Node[P]) -> None: ...
    def dequeue(self) -> Node[P] | None: ...
    def get_lower_bound(self) -> Node[P] | None: ...
    def pop_lower_bound(self) -> Node[P] | None: ...
    def filter_by_lb(self, max_lb: float) -> None: ...
    def clear(self) -> None: ...
    def pop_all(self) -> list[Node[P]]: ...
    def reset_level(self) -> None:
        """Reset the current level pointer back to the first level."""
        ...
