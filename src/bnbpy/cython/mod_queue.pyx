# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

import heapq
import time

from libc.math cimport INFINITY
from libcpp cimport bool
from collections import defaultdict

from bnbpy.cython.node cimport Node
from bnbpy.cython.priqueue cimport BasePriQueue, DFSPriQueue, NodePriQueue


cdef:
    double LOW_NEG = -INFINITY
    double HIGH_POS = INFINITY


cdef class MultiDFSQueue(BasePriQueue):

    def __init__(self, int restart_freq):
        self.restart_freq = restart_freq
        self.iter_count = 0
        self.current_idx = 0
        self.queues = [DFSPriQueue()]

    cpdef bint not_empty(MultiDFSQueue self):
        cdef:
            DFSPriQueue q
            int N, i

        N = len(self.queues)
        for i in range(N):
            q = self.queues[i]
            if self.queues[i].not_empty():
                return True
        return False

    cpdef void enqueue(MultiDFSQueue self, Node node):
        self.queues[self.current_idx].enqueue(node)

    cpdef Node dequeue(MultiDFSQueue self):
        cdef:
            int N, i
            Node bound_node

        self.iter_count += 1

        # At each restart_freq, start a new queue
        if self.iter_count % self.restart_freq == 0:
            # self.queues = [q for q in self.queues if q.not_empty()]
            bound_node = self.pop_lower_bound()
            self.queues.append(DFSPriQueue())
            self.current_idx = len(self.queues) - 1
            return bound_node

        # Always try to dequeue from the first non-empty queue (cycling)
        if self.queues[self.current_idx].not_empty():
            return self.queues[self.current_idx].dequeue()

        N = len(self.queues)
        for i in range(N):
            if self.queues[i].not_empty():
                self.current_idx = i
                return self.queues[i].dequeue()
        return None

    cpdef Node get_lower_bound(MultiDFSQueue self):
        cdef:
            double best_lb
            int N, i
            Node bound_node, node

        N = len(self.queues)
        best_node = None
        best_lb = LOW_NEG
        for i in range(N):
            if self.queues[i].not_empty():
                node = self.queues[i].get_lower_bound()
                if best_node is None and node is not None:
                    best_node = node
                    best_lb = node.lb
                elif node is not None and node.lb < best_lb:
                    best_node = node
                    best_lb = node.lb
        return best_node

    cpdef Node pop_lower_bound(MultiDFSQueue self):
        cdef:
            double best_lb
            int N, i, best_i
            Node bound_node, node

        N = len(self.queues)
        best_i = -1
        best_node = None
        best_lb = LOW_NEG
        for i in range(N):
            if self.queues[i].not_empty():
                node = self.queues[i].get_lower_bound()
                if best_node is None and node is not None:
                    best_node = node
                    best_lb = node.lb
                elif node is not None and node.lb < best_lb:
                    best_node = node
                    best_lb = node.lb
                    best_i = i
        if best_node is not None:
            return self.queues[best_i].pop_lower_bound()
        return None

    cpdef void filter_by_lb(MultiDFSQueue self, double max_lb):
        cdef:
            DFSPriQueue q
            int N, i

        N = len(self.queues)
        for i in range(N):
            q = self.queues[i]
            if not q.not_empty():
                continue
            q.filter_by_lb(max_lb)
            if not q.not_empty():
                self.queues[i] = None
        self.queues = [q for q in self.queues if q is not None]
        if self.queues:
            self.current_idx = len(self.queues) - 1
        else:
            self.queues = [DFSPriQueue()]
            self.current_idx = 0

    cpdef void clear(MultiDFSQueue self):
        self.iter_count = 0
        self.current_idx = 0
        self.queues = [DFSPriQueue()]


cdef class BestQueueNode:

    def __init__(self, Node node):
        self.node = node
        self.lb = node.lb

    def __lt__(self, BestQueueNode other):
        return self.lb < other.lb



cdef class CycleLevel:

    def __init__(self, int level):
        self.level = level
        self.nodes = []
        self.next = self
        self.prev = self

    cpdef void add_node(self, Node node):
        heapq.heappush(self.nodes, BestQueueNode(node))

    cpdef Node pop_node(self):
        if self.nodes:
            return heapq.heappop(self.nodes).node
        return None

    cpdef void filter(self, double max_lb):
        self.nodes = [n for n in self.nodes if n.lb < max_lb]
        heapq.heapify(self.nodes)

    cdef list[Node] pop_all(self):
        cdef:
            BestQueueNode node
            list[Node] nodes
        if self.nodes:
            nodes = [n.node for n in self.nodes]
            self.nodes = []
            return nodes
        return []


cdef class CycleQueue(BasePriQueue):

    def __init__(self, int max_size=100_000):
        self.levels = []
        self.current_level = None
        self.start_level = None
        self.last_level = None
        self.node_counter = 0
        self.fallback_queue = DFSPriQueue()
        self.max_size = max_size
        self.use_fallback = False
        self.add_level()

    cpdef void add_level(self):
        new_level = CycleLevel(len(self.levels))
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

    cpdef bint not_empty(self):
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

        if self.fallback_queue.not_empty():
            self.node_counter -= 1
            node = self.fallback_queue.dequeue()
            if self.node_counter <= self.max_size // 2:
                self.exit_fallback()
            return node

        if len(self.current_level.nodes) == 0:
            self.current_level = self.start_level

        start = self.current_level
        while len(self.current_level.nodes) == 0:
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
            if len(level.nodes) == 0:
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
            node_counter += len(level.nodes)

        self.fallback_queue.filter_by_lb(max_lb)
        node_counter += self.fallback_queue.c_get_size()
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

        print("Entering fallback, moving nodes back to fallback queue...")
        time.sleep(0.5)  # Simulate time taken to move nodes

        nodes = []
        for level in self.levels:
            nodes.extend(level.pop_all())

        for node in nodes:
            self.fallback_queue.enqueue(node)

    cdef void exit_fallback(self):
        cdef:
            Node node
            list[Node] nodes

        print("Exiting fallback, moving nodes back to cycle queue...")
        time.sleep(0.5)  # Simulate time taken to move nodes
        self.use_fallback = False
        nodes = self.fallback_queue.pop_all()
        for node in nodes:
            if node.level <= self.last_level.level:
                self.levels[node.level].add_node(node)
            else:
                for i in range(node.level - self.last_level.level):
                    self.add_level()
                self.levels[node.level].add_node(node)
