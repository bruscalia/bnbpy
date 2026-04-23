# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

import logging

from libc.math cimport INFINITY
from libcpp cimport bool

from bnbpy.cython.manager cimport BaseNodeManager
from bnbpy.cython.node cimport Node
from bnbpy.cython.priqueue_cpp cimport BestCppPriQueue, DfsCppPriQueue, CppPriorityQueue

log = logging.getLogger(__name__)


cdef:
    double LOW_NEG = -INFINITY
    double HIGH_POS = INFINITY


cdef class CycleLevel:

    @classmethod
    def __class_getitem__(cls, item):
        """Support generic syntax CycleLevel[P] at runtime."""
        return cls

    def __init__(self, int level):
        self.level = level
        self.next = self
        self.prev = self
        self.pri_queue = BestCppPriQueue()

    cpdef int size(self):
        return self.pri_queue.size()

    cpdef void set_queue(self, CppPriorityQueue pri_queue):
        self.pri_queue = pri_queue

    cpdef void add_node(self, Node node):
        self.pri_queue.enqueue(node)

    cpdef Node pop_node(self):
        return self.pri_queue.dequeue()

    cpdef void filter(self, double max_lb):
        self.pri_queue.filter_by_lb(max_lb)

    cpdef double peek_lb(self):
        return self.pri_queue.peek_lb()

    cdef list[Node] pop_all(self):
        return self.pri_queue.pop_all()


cdef class CycleQueue(BaseNodeManager):
    """
    A cycling level-based node manager. Useful for cyclic best-first search.

    Nodes are bucketed by tree level. The manager cycles through each level
    in round-robin order, always dequeuing the best node within the
    current level. When the number of stored nodes exceeds *max_size* the
    manager falls back to a DFS priority queue
    (by default a DFS priority queue)
    until the load drops to half of *max_size*.
    """

    def __init__(self, int max_size=100_000, bool permanent_fallback=False):
        """Initialise the cycle queue.

        Parameters
        ----------
        max_size : int, optional
            Maximum number of nodes before switching to the fallback DFS
            queue, by default 100 000.

        permanent_fallback : bool, optional
            If True, the manager will always use the fallback queue and never
            switch back to the cycle queues, by default False.
        """

        self.levels = []
        self.current_level = None
        self.start_level = None
        self.last_level = None
        self.node_counter = 0
        self.max_size = max_size
        self.use_fallback = False
        self.permanent_fallback = permanent_fallback
        self.add_level()
        self.lb = HIGH_POS
        self.bound_nodes = set()

    cpdef CycleLevel new_level(self, int level):
        new_level = CycleLevel(level)
        return new_level

    cdef void add_level(self):
        cdef:
            CycleLevel new_level

        new_level = self.new_level(len(self.levels))
        if not self.levels:
            self.levels.append(new_level)
            self.current_level = new_level
            self.start_level = new_level
            self.last_level = new_level
        else:
            # Insert in last position
            self.last_level.next = new_level
            new_level.prev = self.last_level
            new_level.next = self.start_level
            self.start_level.prev = new_level
            self.levels.append(new_level)
            self.last_level = new_level

    cpdef int size(self):
        return self.node_counter

    cpdef bool not_empty(self):
        return self.node_counter > 0

    cpdef void enqueue(self, Node node):
        cdef:
            int i

        if not self.use_fallback and self.node_counter > self.max_size:
            self.enter_fallback()

        if node.level > self.last_level.level:
            for i in range(node.level - self.last_level.level):
                self.add_level()

        self.levels[node.level].add_node(node)
        self.node_counter += 1
        self.enqueue_bound_update(node)

        if self.use_fallback and node.level > self.current_level.level:
            self.current_level = self.levels[node.level]

    cpdef Node dequeue(self):
        cdef:
            CycleLevel start
            Node node

        # Current level already set to maximum with nodes
        if self.use_fallback:
            start = self.current_level
            while self.current_level.size() == 0:
                self.current_level = self.current_level.prev
                if self.current_level is start:
                    return None
            node = self.current_level.pop_node()
            self.dequeue_bound_update(node)
            self.node_counter -= 1
            if (
                not self.permanent_fallback
                and self.node_counter <= self.max_size // 2
            ):
                self.exit_fallback()
            return node

        self.current_level = self.current_level.next
        if self.current_level.size() == 0:
            self.current_level = self.start_level

        start = self.current_level
        while self.current_level.size() == 0:
            self.current_level = self.current_level.next
            if self.current_level is start:
                return None

        self.node_counter -= 1
        node = self.current_level.pop_node()
        self.dequeue_bound_update(node)
        return node

    cpdef Node get_lower_bound(self):
        cdef:
            Node node
            Node min_node
            set[Node] bound_nodes
            CycleLevel level
            double min_lb

        # First check bound nodes
        for node in self.bound_nodes:
            return node

        min_lb = HIGH_POS
        min_node = None
        self.bound_nodes.clear()
        for level in self.levels:
            if level.size() == 0 or level.peek_lb() > min_lb:
                continue
            # In this loop, do NOT call bound_nodes
            # directly, as it might be stale
            node = level.get_lower_bound()
            if node.lb <= min_lb:
                bound_nodes = level.get_bound_nodes()
                if node.lb < min_lb:
                    min_lb = node.lb
                    min_node = node
                    self.bound_nodes.clear()
                    self.bound_nodes.update(bound_nodes)
                self.bound_nodes.update(bound_nodes)

        self.lb = min_lb
        return min_node

    cpdef void filter_by_lb(self, double max_lb):
        cdef:
            CycleLevel level
            int node_counter

        node_counter = 0
        for level in self.levels:
            level.filter(max_lb)
            node_counter += level.size()

        self.node_counter = node_counter
        if self.node_counter == 0:
            self.lb = HIGH_POS
            self.bound_nodes.clear()

    cpdef void clear(self):
        self.levels = []
        self.current_level = None
        self.start_level = None
        self.last_level = None
        self.node_counter = 0
        self.add_level()
        self.lb = HIGH_POS
        self.bound_nodes.clear()

    cpdef void reset_level(self):
        self.current_level = self.start_level

    cdef void enter_fallback(self):
        cdef:
            CycleLevel start
            list[Node] nodes

        self.use_fallback = True

        log.info("Entering fallback - Cycle queues are full")

        start = self.last_level
        self.current_level = start
        while self.current_level.size() == 0:
            self.current_level = self.current_level.prev
            if self.current_level is start:
                break

        # nodes = []
        # for level in self.levels:
        #     nodes.extend(level.pop_all())
        # self.current_level = self.start_level


    cdef void exit_fallback(self):
        cdef:
            Node node
            list[Node] nodes

        log.info("Exiting fallback - moving nodes back to cycle queues")

        self.use_fallback = False
        # nodes = self.fallback_queue.pop_all()

        # for node in nodes:
        #     if node.level <= self.last_level.level:
        #         self.levels[node.level].add_node(node)
        #     else:
        #         for i in range(node.level - self.last_level.level):
        #             self.add_level()
        #         self.levels[node.level].add_node(node)
