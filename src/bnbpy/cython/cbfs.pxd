# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool

from collections import defaultdict

from bnbpy.cython.manager cimport BaseNodeManager
from bnbpy.cython.node cimport Node
from bnbpy.cython.priqueue cimport BestPriQueue, DfsPriQueue, PriorityQueue


cdef class CycleLevel:
    cdef public:
        int level
        CycleLevel next
        CycleLevel prev

    cdef:
        PriorityQueue pri_queue

    cpdef int size(self)

    cpdef void set_queue(self, PriorityQueue pri_queue)

    cpdef void add_node(self, Node node)

    cpdef Node pop_node(self)

    cpdef void filter(self, double max_lb)

    cdef list[Node] pop_all(self)


cdef class CycleQueue(BaseNodeManager):

    cdef public:
        list[CycleLevel] levels
        CycleLevel current_level
        CycleLevel start_level
        CycleLevel last_level
        int node_counter
        int max_size
        bool use_fallback
        PriorityQueue fallback_queue

    cpdef CycleLevel new_level(self, int level)

    cdef void add_level(self)

    cpdef int size(self)

    cpdef bool not_empty(self)

    cpdef void enqueue(self, Node node)

    cpdef Node dequeue(self)

    cpdef Node get_lower_bound(self)

    cpdef void filter_by_lb(self, double max_lb)

    cpdef void clear(self)

    cpdef void reset_level(self)

    cdef void enter_fallback(self)

    cdef void exit_fallback(self)
