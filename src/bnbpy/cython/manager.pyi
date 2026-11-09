from typing import Generic, TypeVar

from bnbpy.cython.node import Node
from bnbpy.cython.problem import Problem

P = TypeVar('P', bound=Problem)

class BaseNodeManager(Generic[P]):
    """Base class for managing active nodes in a Branch & Bound search.

    Implements the *Template Method* pattern.  Subclasses **must** implement
    the four abstract hooks:

    *   ``_enqueue`` — add a node to the underlying data structure.
    *   ``_dequeue`` — remove and return the next node.
    *   ``_filter_by_lb`` — physically discard nodes with lb >= max_lb.
    *   ``_clear`` — empty the underlying data structure.

    All other public methods implement the template logic, together with
    the internal (C-level) bound memory, and should not be overridden.

    Nodes removed by ``_filter_by_lb`` should be marked as fathomed
    (not cleaned up), so that saved search trees remain consistent.
    """

    @property
    def bound_memory(self) -> dict[float, set[Node[P]]]:
        """Nodes in the manager grouped by lower bound (read-only)"""
        ...

    @property
    def lb(self) -> float:
        """Lower bound recorded when nodes were enqueued; it may be stale
        until :meth:`get_lower_bound` is called (read-only)"""
        ...

    @property
    def bound_nodes(self) -> set[Node[P]]:
        """Nodes with the minimum lower bound (read-only)"""
        ...

    @property
    def nodecount(self) -> int:
        """Number of nodes in the manager (read-only)"""
        ...

    def size(self) -> int:
        """Returns the number of nodes in the manager."""
        ...

    def not_empty(self) -> bool:
        """Checks if the manager is not empty."""
        ...

    def _enqueue(self, node: Node[P]) -> None:
        """Internal hook — add *node* to the underlying structure."""
        ...

    def _dequeue(self) -> Node[P] | None:
        """Internal hook — remove and return the next node."""
        ...

    def _filter_by_lb(self, max_lb: float) -> None:
        """Internal hook — physically remove nodes with lb >= *max_lb*
        (and mark them with ``node.fathom()``)."""
        ...

    def _clear(self) -> None:
        """Internal hook — empty the underlying data structure."""
        ...

    def enqueue(self, node: Node[P]) -> None:
        """Add *node* and record it in ``bound_memory``."""
        ...

    def enqueue_all(self, nodes: list[Node[P]]) -> None:
        """Add a list of nodes."""
        ...

    def dequeue(self) -> Node[P] | None:
        """Remove and return the next node, updating ``bound_memory``."""
        ...

    def get_lower_bound(self) -> Node[P] | None:
        """Return a node with the minimum lower bound (O(1))."""
        ...

    def clear(self) -> None:
        """Make the manager empty."""
        ...

    def filter_by_lb(self, max_lb: float) -> None:
        """Remove nodes with lb >= *max_lb* and update ``bound_memory``."""
        ...

class LifoManager(BaseNodeManager[P]):
    """Last-In First-Out (stack) node manager."""

    def _enqueue(self, node: Node[P]) -> None: ...
    def _dequeue(self) -> Node[P] | None: ...
    def _clear(self) -> None: ...
    def _filter_by_lb(self, max_lb: float) -> None: ...

class FifoManager(LifoManager[P]):
    """First-In First-Out (queue) node manager."""

    def _dequeue(self) -> Node[P] | None: ...
