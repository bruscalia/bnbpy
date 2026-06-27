# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

from libcpp cimport bool
from libcpp.vector cimport vector

from bnbpy.cython.manager cimport BaseNodeManager
from bnbpy.cython.node cimport Node
from bnbpy.cython.nodequeue cimport NodePriQueueWrapper


cdef class PriorityManagerTemplate(BaseNodeManager):

    cdef:
        NodePriQueueWrapper pq

    cpdef void _enqueue(self, Node node)

    cpdef Node _dequeue(self)

    cpdef void _filter_by_lb(self, double max_lb)

    cpdef void _clear(self)

    cpdef vector[double] make_priority(self, Node node)


cdef class BestFirstSearch(PriorityManagerTemplate):
    cpdef vector[double] make_priority(self, Node node)


cdef class DepthFirstSearch(PriorityManagerTemplate):
    cpdef vector[double] make_priority(self, Node node)