# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

import heapq

from bnbpy.cython.node cimport Node


cdef class NodePriQueue:
    def __init__(self, tuple priority, Node node):
        self.priority = priority
        self.node = node

    def __lt__(self, other):
        return self.priority < other.priority


cdef class BasePriQueue:

    cpdef bint not_empty(BasePriQueue self):
        raise NotImplementedError("Must implement not_empty()")

    cpdef void enqueue(BasePriQueue self, Node node):
        raise NotImplementedError("Must implement enqueue()")

    cpdef Node dequeue(BasePriQueue self):
        raise NotImplementedError("Must implement dequeue()")

    cpdef Node get_lower_bound(BasePriQueue self):
        raise NotImplementedError("Must implement get_lower_bound()")

    cpdef Node pop_lower_bound(BasePriQueue self):
        raise NotImplementedError("Must implement get_lower_bound()")

    cpdef void clear(BasePriQueue self):
        raise NotImplementedError("Must implement clear()")

    cpdef void filter_by_lb(BasePriQueue self, double max_lb):
        # Not implemented, but won't be strictly necessary
        pass


cdef class HeapPriQueue(BasePriQueue):
    def __cinit__(self):
        self._queue = []

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
    cpdef void enqueue(self, Node node):
        # DFS: (-level, lb)
        heapq.heappush(self._queue, init_node_pri_queue((-node.level, node.lb), node))


cdef class BFSPriQueue(HeapPriQueue):
    cpdef void enqueue(BFSPriQueue self, Node node):
        # BFS: (level, lb)
        heapq.heappush(self._queue, init_node_pri_queue((node.level, node.lb), node))


cdef class BestPriQueue(HeapPriQueue):
    cpdef void enqueue(self, Node node):
        # Best-first: (lb, -level)
        heapq.heappush(self._queue, init_node_pri_queue((node.lb, -node.level), node))
