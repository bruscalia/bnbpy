from typing import Generic, TypeVar

from bnbpy.cython.node import Node
from bnbpy.cython.problem import Problem

P = TypeVar('P', bound=Problem)

class BaseNodeManager(Generic[P]):
    """Base class for managing active nodes in a Branch & Bound search.

    Note that due to Cython limitations this class is not implemented as an
    ABC, but subclasses **must** implement:

    *   ``size``
    *   ``not_empty``
    *   ``enqueue``
    *   ``dequeue``
    *   ``get_lower_bound``
    *   ``pop_lower_bound``
    *   ``clear``
    *   ``pop_all``

    ``enqueue_all`` and ``filter_by_lb`` have default implementations that
    may be overridden for better performance.
    """

    def size(self) -> int:
        """Returns the number of nodes in the manager.

        Returns
        -------
        int
            The number of nodes in the manager.
        """
        ...

    def not_empty(self) -> bool:
        """Checks if the priority queue is not empty.

        Returns
        -------
        bool
            True if the queue is not empty, False otherwise.
        """
        ...

    def enqueue(self, node: Node[P]) -> None:
        """Adds a node to the priority queue.

        Parameters
        ----------
        node : Node
            The node to add to the queue.
        """
        ...

    def enqueue_all(self, nodes: list[Node[P]]) -> None:
        """Adds a list of nodes to the queue.
        Might be overridden in subclasses for better performance.

        Parameters
        ----------
        nodes : list[Node]
            The list of nodes to add to the queue.
        """
        ...

    def dequeue(self) -> Node[P] | None:
        """Removes and returns the next evaluated node.

        Returns
        -------
        Node
            The next evaluated node.
        """
        ...

    def get_lower_bound(self) -> Node[P] | None:
        """Gets the node of lower bound but
        does not remove it from the queue.

        Returns
        -------
        Node
            The node with the lowest lower bound.
        """
        ...

    def pop_lower_bound(self) -> Node[P] | None:
        """Removes and returns the node of lower bound.

        Returns
        -------
        Node
            The node with the lowest lower bound.
        """
        ...

    def clear(self) -> None:
        """Makes queue empty."""
        ...

    def filter_by_lb(self, max_lb: float) -> None:
        """Filter nodes by lower bound.
        This method is not implemented in the base class,
        but can be overridden in subclasses.

        Parameters
        ----------
        max_lb : float
            The maximum lower bound value.
        """
        ...

    def pop_all(self) -> list[Node[P]]:
        """Removes and returns all nodes in the manager.

        Returns
        -------
        list[Node]
            A list of all nodes in the manager.
        """
        ...

class LifoManager(BaseNodeManager[P]):
    """Last-In First-Out (stack) node manager.

    :meth:`dequeue` returns the most recently enqueued node.
    :meth:`get_lower_bound` and :meth:`pop_lower_bound` perform a linear
    scan over the stack to find the node with minimum ``lb``.
    """

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

class FifoManager(LifoManager[P]):
    """First-In First-Out (queue) node manager.

    Identical to :class:`LifoManager` except that :meth:`dequeue` returns
    the **oldest** enqueued node (``popleft``).
    """

    def dequeue(self) -> Node[P] | None: ...
