# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

from libc.math cimport INFINITY
from libcpp cimport bool
from libcpp.vector cimport vector

import heapq

from bnbpy.cython.manager cimport BaseNodeManager
from bnbpy.cython.node cimport Node
from bnbpy.cython.problem cimport Problem


cdef class PriEntry:

    @classmethod
    def __class_getitem__(cls, item: type[Problem]):
        """Support generic syntax PriEntry[P] at runtime."""
        if not issubclass(item, Problem):
            raise TypeError(
                "PriEntry can only be parameterized"
                f" with a Problem subclass, got {item}"
            )
        return cls

    def __init__(self, Node node, object priority):
        self.node = node
        self.priority = priority

    def __lt__(self, PriEntry other):
        return self.priority < other.priority

    def __gt__(self, PriEntry other):
        return self.priority > other.priority

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
        self.lb = INFINITY
        self.bound_nodes = set()

    cpdef int size(self):
        return len(self.heap)

    cpdef bool not_empty(self):
        return len(self.heap) > 0

    cpdef void enqueue(self, Node node):
        heapq.heappush(self.heap, self.make_entry(node))
        self.enqueue_bound_update(node)

    cpdef void enqueue_all(self, list[Node] nodes):
        cdef:
            int j, N
            Node node
            PriEntry entry
            list[PriEntry] entries

        N = len(nodes)
        entries = [None] * N
        for j in range(N):
            node = nodes[j]
            entries[j] = self.make_entry(node)
            self.enqueue_bound_update(node)
        self.heap.extend(entries)
        heapq.heapify(self.heap)

    cpdef Node dequeue(self):
        cdef:
            Node node
        if not self.heap:
            return None
        node = heapq.heappop(self.heap).node
        self.dequeue_bound_update(node)
        return node

    cpdef Node get_lower_bound(self):
        cdef:
            Node node
            PriEntry item, min_item

        if not self.heap:
            return None

        for node in self.bound_nodes:
            return node

        min_item = self.heap[0]
        self.bound_nodes.clear()
        for item in self.heap:
            if item.node.lb < min_item.node.lb:
                min_item = item
                self.bound_nodes.clear()
                self.bound_nodes.add(item.node)
            elif item.node.lb == min_item.node.lb:
                self.bound_nodes.add(item.node)
        self.lb = min_item.node.lb
        return min_item.node

    cpdef Node pop_lower_bound(self):
        cdef:
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
        self.dequeue_bound_update(min_item.node)
        return min_item.node

    cpdef void filter_by_lb(self, double max_lb):
        cdef:
            int i, j, N
            PriEntry item

        N = len(self.heap)
        j = 0
        for i in range(N):
            item = self.heap[i]
            if item.node.lb < max_lb:
                self.heap[j] = item
                j += 1
            else:
                item.node.cleanup()
        self.heap = self.heap[:j]
        heapq.heapify(self.heap)
        if len(self.heap) == 0:
            self.lb = INFINITY
            self.bound_nodes.clear()

    cpdef void clear(self):
        self.heap.clear()
        self.lb = INFINITY
        self.bound_nodes.clear()

    cpdef list[Node] pop_all(self):
        cdef:
            PriEntry item
            list[Node] nodes
        nodes = [item.node for item in self.heap]
        self.heap.clear()
        self.lb = INFINITY
        self.bound_nodes.clear()
        return nodes

    cpdef list[PriEntry] get_heap(self):
        return self.heap

    cpdef PriEntry make_entry(self, Node node):
        """Return a :class:`PriEntry` for *node*.

        Subclasses must override this to define the ordering key.

        Parameters
        ----------
        node : Node[P]
            Node to wrap.

        Returns
        -------
        PriEntry[P]
            Heap entry carrying *node* and its ordering priority.
        """
        raise NotImplementedError("Subclasses must implement `make_entry` method")

    cpdef double peek_lb(self):
        return self.lb

    cpdef set[Node] get_bound_nodes(self):
        return self.bound_nodes


cdef class DfsPriQueue(PriorityQueue):
    """
    Depth-First Search priority queue implementation with
    tie-breaking by lower bound and node index (greater first).
    """

    cpdef PriEntry make_entry(self, Node node):
        # DFS: (-level, lb)
        return init_pri_entry(
            node,
            (-node.level, node.lb, -node.get_index())
        )


cdef class BfsPriQueue(PriorityQueue):
    """
    Breadth-First Search priority queue implementation with
    tie-breaking by lower bound and node index (smaller first).
    """

    cpdef PriEntry make_entry(self, Node node):
        # BFS: (level, lb)
        return init_pri_entry(
            node,
            (node.level, node.lb, node.get_index())
        )


cdef class BestPriQueue(PriorityQueue):
    """
    Best-First Search priority queue implementation.

    Nodes are ordered by lower bound, with tie-breaking by tree level
    (deeper nodes first) and node index (greater first).
    """

    cpdef PriEntry make_entry(self, Node node):
        # Best-first: (lb, -level, -index) — deeper nodes break ties
        return init_pri_entry(
            node,
            (node.lb, -node.level, -node.get_index())
        )
