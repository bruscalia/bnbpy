from typing import Any

from bnbpy.cython.node import Node

class NodePriQueue:
    priority: tuple[Any, ...]
    node: Node

    def __init__(self, priority: tuple[Any, ...], node: Node) -> None:
        ...

class BasePriQueue:

    def not_empty(self) -> bool:
        """Checks if the priority queue is not empty.

        Returns
        -------
        bool
            True if the queue is not empty, False otherwise.
        """
        ...

    def enqueue(self, node: Node) -> None:
        """Adds a node to the priority queue.

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
            The next evaluated node.
        """
        ...

    def get_lower_bound(self) -> Node:
        """Gets the node of lower bound but
        does not remove it from the queue.

        Returns
        -------
        Node
            The node with the lowest lower bound.
        """
        ...

    def pop_lower_bound(self) -> Node:
        """Removes and returns the node of lower bound.

        Returns
        -------
        Node
            The node with the lowest lower bound.
        """
        ...

    def clear(self) -> None:
        """Makes queue empty.
        """
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

    def not_empty(self) -> bool:
        ...

    def dequeue(self) -> Node:
        ...

    def get_lower_bound(self) -> Node:
        ...

    def pop_lower_bound(self) -> Node:
        ...

    def clear(self) -> None:
        ...

    def filter_by_lb(self, max_lb: float) -> None:
        """Filters the nodes in the priority queue by their lower bound.

        Parameters
        ----------
        max_lb : float
            The maximum lower bound value.
        """
        ...

class DFSPriQueue(HeapPriQueue):

    def enqueue(self, node: Node) -> None:
        ...

class BFSPriQueue(HeapPriQueue):

    def enqueue(self, node: Node) -> None:
        ...

class BestPriQueue(HeapPriQueue):

    def enqueue(self, node: Node) -> None:
        ...
