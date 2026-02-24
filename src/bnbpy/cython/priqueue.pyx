# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libc.math cimport INFINITY

import heapq

from bnbpy.cython.node cimport Node


cdef class NodePriQueue:
    def __init__(self, tuple priority, Node node):
        self.priority = priority
        self.node = node

    def __lt__(self, other):
        return self.priority < other.priority


cdef class BasePriQueue:
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

    cpdef bint not_empty(BasePriQueue self):
        """Checks if the priority queue is not empty.

        Returns
        -------
        bool
            True if the queue is not empty, False otherwise.
        """
        raise NotImplementedError("Must implement not_empty()")

    cpdef void enqueue(BasePriQueue self, Node node):
        """Adds a node to the priority queue.

        Parameters
        ----------
        node : Node
            The node to add to the queue.
        """
        raise NotImplementedError("Must implement enqueue()")

    cpdef Node dequeue(BasePriQueue self):
        """Removes and returns the next evaluated node.

        Returns
        -------
        Node
            The next evaluated node.
        """
        raise NotImplementedError("Must implement dequeue()")

    cpdef Node get_lower_bound(BasePriQueue self):
        """Gets the node of lower bound but
        does not remove it from the queue.

        Returns
        -------
        Node
            The node with the lowest lower bound.
        """
        raise NotImplementedError("Must implement get_lower_bound()")

    cpdef Node pop_lower_bound(BasePriQueue self):
        """Removes and returns the node of lower bound.

        Returns
        -------
        Node
            The node with the lowest lower bound.
        """
        raise NotImplementedError("Must implement pop_lower_bound()")

    cpdef void clear(BasePriQueue self):
        """Makes queue empty."""
        raise NotImplementedError("Must implement clear()")

    cpdef void filter_by_lb(BasePriQueue self, double max_lb):
        """Filter nodes by lower bound.
        This method is not implemented in the base class,
        but can be overridden in subclasses.

        Parameters
        ----------
        max_lb : float
            The maximum lower bound value.
        """
        # Not implemented, but won't be strictly necessary
        pass


cdef class HeapPriQueue(BasePriQueue):
    def __cinit__(self):
        self._queue = []
        self.lb = -INFINITY

    cpdef bint not_empty(HeapPriQueue self):
        return bool(self._queue)

    cpdef Node dequeue(HeapPriQueue self):
        if self.not_empty():
            return heapq.heappop(self._queue).node
        return None

    cpdef Node get_lower_bound(HeapPriQueue self):
        cdef:
            Node node
            NodePriQueue item
        if not self._queue:
            return None
        node = self._queue[0].node
        for item in self._queue:
            if item.node.lb < node.lb:
                node = item.node
                if node.lb <= self.lb:
                    break
        self.lb = node.lb
        return node

    cpdef Node pop_lower_bound(HeapPriQueue self):
        cdef:
            NodePriQueue item, min_item
        if not self._queue:
            return None
        min_item = self._queue[0]
        for item in self._queue:
            if item.node.lb < min_item.node.lb:
                min_item = item
        self._queue.remove(min_item)
        return min_item.node

    cpdef void filter_by_lb(HeapPriQueue self, double max_lb):
        cdef:
            int i, N
            NodePriQueue item
            list[NodePriQueue] new_queue

        N = len(self._queue)
        new_queue = []
        for i in range(N):
            item = self._queue[i]
            if item.node.lb < max_lb:
                new_queue.append(item)
        self._queue = new_queue

    cpdef void clear(HeapPriQueue self):
        self._queue = []


cdef class DFSPriQueue(HeapPriQueue):
    """Depth-First Search priority queue implementation."""

    cpdef void enqueue(self, Node node):
        # DFS: (-level, lb)
        heapq.heappush(
            self._queue,
            init_node_pri_queue((-node.level, node.lb, node.get_index()), node)
        )


cdef class BFSPriQueue(HeapPriQueue):
    """Breadth-First Search priority queue implementation."""

    cpdef void enqueue(BFSPriQueue self, Node node):
        # BFS: (level, lb)
        heapq.heappush(
            self._queue, init_node_pri_queue((node.level, node.lb, node.get_index()), node)
        )


cdef class BestPriQueue(HeapPriQueue):
    """Best-First Search priority queue implementation."""

    cpdef void enqueue(self, Node node):
        # Best-first: (lb, -level)
        heapq.heappush(
            self._queue,
            init_node_pri_queue((node.lb, -node.level, node.get_index()), node)
        )
