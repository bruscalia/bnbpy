# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

from libcpp cimport bool
from libcpp.vector cimport vector

from bnbpy.cython.manager cimport BaseNodeManager
from bnbpy.cython.node cimport Node
from bnbpy.cython.nodequeue cimport NodePriQueueWrapper


cdef class PriorityManagerTemplate(BaseNodeManager):
    """Priority queue manager backed by a native C++ binary heap.

    Stores nodes with ``vector[double]`` priorities; the queue is a
    *min*-heap (smallest priority dequeued first).

    Subclasses must override :meth:`make_priority`.
    """

    def __cinit__(self):
        self.pq = NodePriQueueWrapper()

    cpdef void _enqueue(self, Node node):
        self.pq.push(node, self.make_priority(node))

    cpdef Node _dequeue(self):
        return self.pq.pop()

    cpdef void _filter_by_lb(self, double max_lb):
        self.pq.filter(max_lb)

    cpdef void _clear(self):
        self.pq.clear()

    cpdef vector[double] make_priority(self, Node node):
        raise NotImplementedError(
            "Subclasses must implement make_priority()"
        )


cdef class BestFirstSearch(PriorityManagerTemplate):
    """Best-first variant: priority ``(lb, -level, -index)``."""
    cpdef vector[double] make_priority(self, Node node):
        cdef:
            vector[double] pri = vector[double](3)
        pri[0] = node.lb
        pri[1] = -node.level
        pri[2] = -node.get_index()
        return pri


cdef class DepthFirstSearch(PriorityManagerTemplate):
    """Depth-first variant: priority ``(-level, lb, -index)``."""
    cpdef vector[double] make_priority(self, Node node):
        cdef:
            vector[double] pri = vector[double](3)
        pri[0] = -node.level
        pri[1] = node.lb
        pri[2] = -node.get_index()
        return pri
