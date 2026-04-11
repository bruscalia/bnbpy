# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libc.math cimport INFINITY
from libcpp cimport bool
from libcpp.vector cimport vector

import heapq

from bnbpy.cython.manager cimport BaseNodeManager
from bnbpy.cython.node cimport Node


cdef class PriEntry:

    def __init__(self, Node node, object priority):
        self.node = node
        self.priority = priority

    def __lt__(self, PriEntry other):
        return self.priority < other.priority

    cpdef object get_priority(self):
        return self.priority


cdef class PriorityQueue(BaseNodeManager):
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

    def __cinit__(self):
        self.heap = []
        self.lb = -INFINITY

    cpdef int size(self):
        return len(self.heap)

    cpdef bool not_empty(self):
        return len(self.heap) > 0

    cpdef Node dequeue(self):
        if self.not_empty():
            return heapq.heappop(self.heap).node
        return None

    cpdef Node get_lower_bound(self):
        cdef:
            Node node
            PriEntry item, min_item

        if not self.heap:
            return None

        min_item = self.heap[0]
        for item in self.heap:
            if item.node.lb < min_item.node.lb:
                min_item = item
                if item.node.lb <= self.lb:
                    break
        self.lb = min_item.node.lb
        return min_item.node

    cpdef Node pop_lower_bound(self):
        cdef:
            Node node
            PriEntry item, min_item

        if not self.heap:
            return None

        min_item = self.heap[0]
        for item in self.heap:
            if item.node.lb < min_item.node.lb:
                min_item = item
                if item.node.lb <= self.lb:
                    break
        self.lb = min_item.node.lb
        self.heap.remove(min_item)
        return min_item.node

    cpdef void filter_by_lb(self, double max_lb):
        cdef:
            PriEntry item
            list[PriEntry] new_queue

        new_queue = [item for item in self.heap if item.node.lb < max_lb]
        self.heap = new_queue

    cpdef void clear(self):
        self.heap.clear()

    cpdef list[Node] pop_all(self):
        cdef:
            PriEntry item
            list[Node] nodes
        nodes = [item.node for item in self.heap]
        self.heap.clear()
        return nodes

    cpdef list[PriEntry] get_heap(self):
        return self.heap

    cpdef void enqueue_entry(self, Node node, object priority):
        heapq.heappush(self.heap, init_pri_entry(node, priority))


cdef class DfsPriQueue(PriorityQueue):
    """
    Depth-First Search priority queue implementation with
    tie-breaking by lower bound and node index (smaller first).
    """

    cpdef void enqueue(self, Node node):
        # DFS: (-level, lb)
        self.enqueue_entry(
            node,
            (-node.level, node.lb, node.get_index())
        )


cdef class BfsPriQueue(PriorityQueue):
    """
    Breadth-First Search priority queue implementation with
    tie-breaking by lower bound and node index (smaller first).
    """

    cpdef void enqueue(self, Node node):
        # BFS: (level, lb)
        self.enqueue_entry(
            node,
            (node.level, node.lb, node.get_index())
        )


cdef class BestPriQueue(PriorityQueue):
    """
    Best-First Search priority queue implementation.
    """

    cpdef void enqueue(self, Node node):
        # Best-first: (lb)
        self.enqueue_entry(
            node,
            node.lb
        )

    cpdef Node get_lower_bound(self):
        cdef:
            Node node
            PriEntry item
        if self.not_empty():
            item = heapq.heapop(self.heap)
            node = item.node
            heapq.heappush(self.heap, item)
            return node
        return None

    cpdef Node pop_lower_bound(BestPriQueue self):
        if self.not_empty():
            return heapq.heappop(self.heap).node
        return None
