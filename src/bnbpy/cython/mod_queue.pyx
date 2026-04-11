# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

import heapq
import logging
import time

from libc.math cimport INFINITY
from libcpp cimport bool
from collections import defaultdict

from bnbpy.cython.manager cimport BaseNodeManager
from bnbpy.cython.node cimport Node
from bnbpy.cython.priqueue cimport BestPriQueue, DfsPriQueue, PriorityQueue

log = logging.getLogger(__name__)


cdef:
    double LOW_NEG = -INFINITY
    double HIGH_POS = INFINITY


cdef class CycleLevel:

    def __init__(self, int level):
        self.level = level
        self.next = self
        self.prev = self
        self.pri_queue = BestPriQueue()

    cpdef int size(self):
        return self.pri_queue.size()

    cpdef void set_queue(self, PriorityQueue pri_queue):
        self.pri_queue = pri_queue

    cpdef void add_node(self, Node node):
        self.pri_queue.enqueue(node)

    cpdef Node pop_node(self):
        return self.pri_queue.dequeue()

    cpdef void filter(self, double max_lb):
        self.pri_queue.filter_by_lb(max_lb)

    cdef list[Node] pop_all(self):
        return self.pri_queue.pop_all()


cdef class CycleQueue(BaseNodeManager):

    def __init__(self, int max_size=100_000):
        self.levels = []
        self.current_level = None
        self.start_level = None
        self.last_level = None
        self.node_counter = 0
        self.fallback_queue = DfsPriQueue()
        self.max_size = max_size
        self.use_fallback = False
        self.add_level()

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

        if self.use_fallback:
            self.fallback_queue.enqueue(node)
            self.node_counter += 1
            return

        if node.level <= self.last_level.level:
            self.levels[node.level].add_node(node)
        else:
            for i in range(node.level - self.last_level.level):
                self.add_level()
            self.levels[node.level].add_node(node)
        self.node_counter += 1

    cpdef Node dequeue(self):
        cdef:
            CycleLevel start
            Node node

        if self.use_fallback or self.fallback_queue.not_empty():
            self.node_counter -= 1
            node = self.fallback_queue.dequeue()
            if self.node_counter <= self.max_size // 2:
                self.exit_fallback()
            return node

        if self.current_level.size() == 0:
            self.current_level = self.start_level

        start = self.current_level
        while self.current_level.size() == 0:
            self.current_level = self.current_level.next
            if self.current_level == start:
                return None

        self.node_counter -= 1
        node = self.current_level.pop_node()
        self.current_level = self.current_level.next
        return node

    cpdef Node get_lower_bound(self):
        cdef:
            Node node
            Node min_node
            CycleLevel level
            double min_lb

        min_lb = HIGH_POS
        min_node = None
        for level in self.levels:
            if level.size() == 0:
                continue
            node = level.pop_node()
            if node.lb < min_lb:
                min_lb = node.lb
                min_node = node
            level.add_node(node)

        if self.fallback_queue.not_empty():
            node = self.fallback_queue.get_lower_bound()
            if node is not None and node.lb < min_lb:
                min_node = node
        return min_node

    cpdef void filter_by_lb(self, double max_lb):
        cdef:
            CycleLevel level
            int node_counter

        node_counter = 0
        for level in self.levels:
            level.filter(max_lb)
            node_counter += level.size()

        self.fallback_queue.filter_by_lb(max_lb)
        node_counter += self.fallback_queue.size()
        self.node_counter = node_counter

    cpdef void clear(self):
        self.levels = []
        self.current_level = None
        self.start_level = None
        self.last_level = None
        self.node_counter = 0
        self.fallback_queue.clear()
        self.add_level()

    cpdef void reset_level(self):
        self.current_level = self.start_level

    cdef void enter_fallback(self):
        cdef:
            CycleLevel level
            Node node
            list[Node] nodes

        self.use_fallback = True

        log.info("Entering fallback - Cycle queues are full")

        nodes = []
        for level in self.levels:
            nodes.extend(level.pop_all())

        for node in nodes:
            self.fallback_queue.enqueue(node)

    cdef void exit_fallback(self):
        cdef:
            Node node
            list[Node] nodes

        log.info("Exiting fallback - moving nodes back to cycle queues")

        self.use_fallback = False
        nodes = self.fallback_queue.pop_all()
        for node in nodes:
            if node.level <= self.last_level.level:
                self.levels[node.level].add_node(node)
            else:
                for i in range(node.level - self.last_level.level):
                    self.add_level()
                self.levels[node.level].add_node(node)
