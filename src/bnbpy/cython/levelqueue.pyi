from typing import Generic, TypeVar

from bnbpy.cython.manager import BaseNodeManager
from bnbpy.cython.node import Node
from bnbpy.cython.nodequeue import PriorityManagerInterface
from bnbpy.cython.problem import Problem

P = TypeVar('P', bound=Problem)

class LevelQueue(Generic[P]):
    """A single level in a level-based node manager.

    Internally holds a
    :class:`~bnbpy.cython.nodequeue.PriorityManagerInterface`
    (``queue`` attribute) and maintains doubly-linked pointers to neighbouring
    levels.
    """

    level: int
    next: 'LevelQueue[P]'
    prev: 'LevelQueue[P]'
    queue: PriorityManagerInterface[P]

    def __init__(self, level: int) -> None: ...
    def size(self) -> int:
        """Return the number of nodes at this level."""
        ...

    def set_queue(self, queue: PriorityManagerInterface[P]) -> None:
        """Replace the internal priority queue.

        Parameters
        ----------
        queue : PriorityManagerInterface[P]
            New priority queue to use at this level.
        """
        ...

    def add_node(self, node: Node[P]) -> None:
        """Enqueue *node* at this level."""
        ...

    def pop_node(self) -> Node[P] | None:
        """Dequeue and return the next node at this level."""
        ...

    def filter(self, max_lb: float) -> None:
        """Discard nodes whose ``lb >= max_lb``."""
        ...

    def peek_lb(self) -> float:
        """Return the current lower-bound of this level without popping."""
        ...

class LevelManagerInterface(BaseNodeManager[P]):
    """Abstract base for level-based node managers.

    Nodes are bucketed by tree level.  Concrete subclasses must override
    :meth:`new_level` to define which
    :class:`~bnbpy.cython.nodequeue.PriorityManagerInterface` is used at
    each level.
    """

    levels: list[LevelQueue[P]]
    current_level: LevelQueue[P]
    start_level: LevelQueue[P]
    last_level: LevelQueue[P]
    node_counter: int
    max_size: int
    use_fallback: bool
    permanent_fallback: bool

    def __init__(
        self,
        max_size: int = 100_000,
        permanent_fallback: bool = False,
    ) -> None: ...
    def new_level(self, level: int) -> LevelQueue[P]:
        """Create a new :class:`LevelQueue` for the given tree depth.

        Must be overridden by subclasses.

        Parameters
        ----------
        level : int
            Tree depth of the new level.
        """
        ...

    def size(self) -> int: ...
    def not_empty(self) -> bool: ...
    def enqueue(self, node: Node[P]) -> None: ...
    def enqueue_all(self, nodes: list[Node[P]]) -> None: ...
    def dequeue(self) -> Node[P] | None: ...
    def get_lower_bound(self) -> Node[P] | None: ...
    def pop_lower_bound(self) -> Node[P] | None: ...
    def filter_by_lb(self, max_lb: float) -> None: ...
    def clear(self) -> None: ...
    def pop_all(self) -> list[Node[P]]: ...
    def reset_level(self) -> None:
        """Reset the current level pointer back to the first level."""
        ...

class CyclicBestSearch(LevelManagerInterface[P]):
    """Cyclic best-first search node manager.

    Cycles through tree levels in round-robin order, dequeuing the best
    (lowest-lb) node within each level.  Switches to deepest-level-first
    when the total node count exceeds *max_size*.
    """

    def __init__(
        self,
        max_size: int = 100_000,
        permanent_fallback: bool = False,
    ) -> None: ...
    def new_level(self, level: int) -> LevelQueue[P]: ...

class DfsPriority(LevelManagerInterface[P]):
    """Depth-first priority node manager.

    Always dequeues the best node (lowest lb) from the deepest non-empty
    level.  Equivalent to :class:`CyclicBestSearch` with permanent fallback
    engaged from the start.
    """

    def __init__(self) -> None: ...
    def new_level(self, level: int) -> LevelQueue[P]: ...
