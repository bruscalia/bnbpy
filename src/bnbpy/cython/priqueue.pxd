# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector

from bnbpy.cython.manager cimport BaseNodeManager
from bnbpy.cython.node cimport Node


cdef class PriEntry:
    cdef readonly:
        Node node
        object priority

    cpdef object get_priority(self)


cdef inline PriEntry init_pri_entry(Node node, object priority):

    cdef:
        PriEntry npri
    npri = PriEntry.__new__(PriEntry)
    npri.priority = priority
    npri.node = node
    return npri


cdef class PriorityQueue(BaseNodeManager):

    cdef:
        list[PriEntry] heap
        double lb

    cpdef int size(self)

    cpdef bool not_empty(self)

    cpdef void enqueue(self, Node node)

    cpdef void enqueue_all(self, list[Node] nodes)

    cpdef Node dequeue(self)

    cpdef Node get_lower_bound(self)

    cpdef Node pop_lower_bound(self)

    cpdef void filter_by_lb(self, double max_lb)

    cpdef void clear(self)

    cpdef list[Node] pop_all(self)

    cpdef list[PriEntry] get_heap(self)

    cpdef PriEntry make_entry(self, Node node)


cdef class DfsPriQueue(PriorityQueue):

    cpdef PriEntry make_entry(self, Node node)


cdef class BfsPriQueue(PriorityQueue):

    cpdef PriEntry make_entry(self, Node node)


cdef class BestPriQueue(PriorityQueue):

    cpdef PriEntry make_entry(self, Node node)

