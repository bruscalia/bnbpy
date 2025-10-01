# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from collections import defaultdict

from bnbpy.cython.node cimport Node
from bnbpy.cython.priqueue cimport BasePriQueue, DFSPriQueue, NodePriQueue


cdef class MultiDFSQueue(BasePriQueue):

    cdef public:
        list[DFSPriQueue] queues
        int restart_freq
        int iter_count
        int current_idx

    cpdef bint not_empty(MultiDFSQueue self)

    cpdef void enqueue(MultiDFSQueue self, Node node)

    cpdef Node dequeue(MultiDFSQueue self)

    cpdef Node get_lower_bound(MultiDFSQueue self)

    cpdef Node pop_lower_bound(MultiDFSQueue self)

    cpdef void filter_by_lb(MultiDFSQueue self, double max_lb)

    cpdef void clear(MultiDFSQueue self)


cdef class CycleQueue(BasePriQueue):

    cdef public:
        object queues

    cdef:
        int max_level
        int current_level

    cpdef bint not_empty(CycleQueue self)

    cpdef void enqueue(CycleQueue self, Node node)

    cpdef Node dequeue(CycleQueue self)

    cpdef Node get_lower_bound(CycleQueue self)

    cpdef void filter_by_lb(CycleQueue self, double max_lb)

    cpdef void clear(CycleQueue self)

    cpdef void reset_level(CycleQueue self)
