# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libc.math cimport INFINITY
from collections import defaultdict

from bnbpy.cython.node cimport Node
from bnbpy.cython.priqueue cimport BasePriQueue, DFSPriQueue, NodePriQueue


cdef:
    double LOW_NEG = -INFINITY


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


cdef class CycleQueue(BasePriQueue):

    def __init__(self):
        self.queues = defaultdict(DFSPriQueue)
        self.max_level = 0
        self.current_level = 0

    cpdef bint not_empty(CycleQueue self):
        cdef:
            DFSPriQueue q
        for q in self.queues.values():
            if q.not_empty():
                return True
        return False

    cpdef void enqueue(CycleQueue self, Node node):
        self.queues[node.level].enqueue(node)
        self.max_level = max(self.max_level, node.level)

    cpdef Node dequeue(CycleQueue self):
        cdef:
            int start_level
            Node node

        self.current_level = (self.current_level + 1) % (self.max_level + 1)
        start_level = self.current_level
        while True:
            if self.queues[self.current_level].not_empty():
                return self.queues[self.current_level].dequeue()

            # Cycle to the next level
            self.current_level = (self.current_level + 1) % (self.max_level + 1)

            # If we've cycled back to the starting point and found nothing, stop
            if self.current_level == start_level:
                return None

    cpdef Node get_lower_bound(CycleQueue self):
        cdef:
            NodePriQueue node
            NodePriQueue min_node = None
            int level

        for level in range(self.max_level + 1):
            for node in self.queues[level]._queue:
                if min_node is None:
                    min_node = node
                if node.node.lb < min_node.node.lb:
                    min_node = node
        return min_node.node

    cpdef void filter_by_lb(CycleQueue self, double max_lb):
        self.queues[self.current_level].filter_by_lb(max_lb)

    cpdef void clear(CycleQueue self):
        self.queues = defaultdict(DFSPriQueue)
        self.max_level = 0
        self.current_level = 0

    cpdef void reset_level(CycleQueue self):
        self.current_level = 0
