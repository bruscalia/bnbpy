from typing import Generic, TypeVar

from bnbpy.cython.manager import BaseNodeManager
from bnbpy.cython.node import Node
from bnbpy.cython.problem import Problem

P = TypeVar('P', bound=Problem)

class LevelQueue(Generic[P]):
    """A single level in a level-based node manager.

    Internally holds a raw C++ min-heap (``NodePriQueue``) and maintains
    doubly-linked pointers to neighbouring levels.  Nodes are ordered by the
    key produced by :meth:`make_priority`.
    """

    level: int
    next: 'LevelQueue[P]'
    prev: 'LevelQueue[P]'

    def __init__(self, level: int) -> None: ...
    def size(self) -> int:
        """Return the number of nodes at this level."""
        ...

    def make_priority(self, node: Node[P]) -> list[float]:
        """Return the ordering key for *node* (smaller → dequeued first).

        Default is best-first: ``(lb, -level, -index)``.  Override in
        subclasses to change intra-level ordering.

        Parameters
        ----------
        node : Node
            The node being enqueued.

        Returns
        -------
        list[float]
            Priority vector; smaller values are dequeued first.
        """
        ...

    def push(self, node: Node[P]) -> None:
        """Enqueue *node* at this level.

        Parameters
        ----------
        node : Node
            The node to enqueue.
        """
        ...

    def pop(self) -> Node[P] | None:
        """Dequeue and return the highest-priority node at this level.

        Returns
        -------
        Node or None
            The node with the smallest priority key, or ``None`` if this
            level is empty.
        """
        ...

    def filter(self, max_lb: float) -> None:
        """Discard nodes whose ``lb >= max_lb``."""
        ...

class LevelManagerInterface(BaseNodeManager[P]):
    """Abstract base for level-based node managers.

    Nodes are bucketed by tree level.  Concrete subclasses must override
    :meth:`new_level` to define which :class:`LevelQueue` subclass is used
    at each level.
    """

    levels: list[LevelQueue[P]]
    current_level: LevelQueue[P]
    start_level: LevelQueue[P]
    last_level: LevelQueue[P]
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

    def _enqueue(self, node: Node[P]) -> None: ...
    def _dequeue(self) -> Node[P] | None: ...
    def _filter_by_lb(self, max_lb: float) -> None: ...
    def _clear(self) -> None: ...
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
