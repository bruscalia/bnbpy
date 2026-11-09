from typing import TypeVar

from bnbpy.cython.node import Node
from bnbpy.cython.problem import Problem

P = TypeVar('P', bound=Problem)

class NodePriQueueWrapper:
    """Min-heap of nodes with ``vector[double]`` priorities, backed by a
    native C++ binary heap (lexicographic order; smallest first).

    Low-level building block of
    :class:`~bnbpy.cython.primanager.PriorityManagerTemplate` and
    :class:`~bnbpy.cython.levelqueue.LevelQueue`.
    It does not track lower bounds by itself.
    """

    def push(self, node: Node[P], priority: list[float]) -> None:
        """Insert *node* with the given priority vector."""
        ...

    def pop(self) -> Node[P] | None:
        """Remove and return the node with the smallest priority,
        or ``None`` if empty."""
        ...

    def filter(self, max_lb: float) -> None:
        """Remove the nodes with ``lb >= max_lb`` (lower bound at insertion)
        and mark them as fathomed."""
        ...

    def size(self) -> int:
        """Number of nodes in the heap."""
        ...

    def clear(self) -> None:
        """Remove all nodes."""
        ...
