# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool

from collections import defaultdict

from bnbpy.cython.node cimport Node
from bnbpy.cython.priqueue cimport BasePriQueue, DFSPriQueue, HeapPriQueue, NodePriQueue


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


cdef class BestQueueNode:
    cdef public:
        Node node
        double lb


cdef class CycleLevel:
    cdef public:
        int level
        list[BestQueueNode] nodes
        CycleLevel next
        CycleLevel prev

    cpdef void add_node(self, Node node)

    cpdef Node pop_node(self)

    cpdef void filter(self, double max_lb)

    cdef list[Node] pop_all(self)


cdef class CycleQueue(BasePriQueue):

    cdef public:
        list[CycleLevel] levels
        CycleLevel current_level
        CycleLevel start_level
        CycleLevel last_level
        int node_counter
        int max_size
        bool use_fallback
        HeapPriQueue fallback_queue

    cpdef void add_level(self)

    cpdef bint not_empty(self)

    cpdef void enqueue(self, Node node)

    cpdef Node dequeue(self)

    cpdef Node get_lower_bound(self)

    cpdef void filter_by_lb(self, double max_lb)

    cpdef void clear(self)

    cpdef void reset_level(self)

    cdef void enter_fallback(self)

    cdef void exit_fallback(self)
