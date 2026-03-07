from abc import abstractmethod
from typing import Any

from bnbpy.cython.node import Node

class NodePriQueue:
    priority: tuple[Any, ...]
    node: Node

    def __init__(self, priority: tuple[Any, ...], node: Node) -> None: ...
    def __lt__(self, other: 'NodePriQueue') -> bool: ...

class BasePriQueue:
    """
    Base class for managing active nodes in Branch & Bound algorithm
    (not necessarily formally implementing a priority queue).

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

    @abstractmethod
    def not_empty(self) -> bool:
        """Checks if the priority queue is not empty.

        Returns
        -------
        bool
            True if the queue is not empty, False otherwise.
        """
        ...

    @abstractmethod
    def enqueue(self, node: Node) -> None:
        """Adds a node to the priority queue.

        Parameters
        ----------
        node : Node
            The node to add to the queue.
        """
        ...

    @abstractmethod
    def dequeue(self) -> Node:
        """Removes and returns the next evaluated node.

        Returns
        -------
        Node
            The next evaluated node.
        """
        ...

    @abstractmethod
    def get_lower_bound(self) -> Node:
        """Gets the node of lower bound but
        does not remove it from the queue.

        Returns
        -------
        Node
            The node with the lowest lower bound.
        """
        ...

    @abstractmethod
    def pop_lower_bound(self) -> Node:
        """Removes and returns the node of lower bound.

        Returns
        -------
        Node
            The node with the lowest lower bound.
        """
        ...

    @abstractmethod
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

class HeapPriQueue(BasePriQueue):
    _queue: list[NodePriQueue]

    def __cinit__(self) -> None: ...
    def not_empty(self) -> bool: ...
    def enqueue(self, node: Node) -> None:
        """Adds a node to the priority queue.
        Base implementation raises NotImplementedError.

        Parameters
        ----------
        node : Node
            The node to add to the queue.
        """
        ...

    def dequeue(self) -> Node:
        """Removes and returns the next evaluated node.

        Returns
        -------
        Node
            The next evaluated node, or None if queue is empty.
        """
        ...

    def get_lower_bound(self) -> Node:
        """Gets the node of lower bound but does not remove it from the queue.

        Returns
        -------
        Node
            The node with the lowest lower bound, or None if queue is empty.
        """
        ...

    def pop_lower_bound(self) -> Node:
        """Removes and returns the node of lower bound.

        Returns
        -------
        Node
            The node with the lowest lower bound, or None if queue is empty.
        """
        ...

    def clear(self) -> None: ...
    def filter_by_lb(self, max_lb: float) -> None:
        """Filters the nodes in the priority queue by their lower bound.

        Parameters
        ----------
        max_lb : float
            The maximum lower bound value.
        """
        ...

class DFSPriQueue(HeapPriQueue):
    """Depth-First Search priority queue implementation."""

    def enqueue(self, node: Node) -> None:
        """Enqueue node using DFS priority: (-level, lb).

        Parameters
        ----------
        node : Node
            The node to add to the queue.
        """
        ...

class BFSPriQueue(HeapPriQueue):
    """Breadth-First Search priority queue implementation."""

    def enqueue(self, node: Node) -> None:
        """Enqueue node using BFS priority: (level, lb).

        Parameters
        ----------
        node : Node
            The node to add to the queue.
        """
        ...

class BestPriQueue(HeapPriQueue):
    """Best-First Search priority queue implementation."""

    def enqueue(self, node: Node) -> None:
        """Enqueue node using best-first priority: (lb, -level).

        Parameters
        ----------
        node : Node
            The node to add to the queue.
        """
        ...
