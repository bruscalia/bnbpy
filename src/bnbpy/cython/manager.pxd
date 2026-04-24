# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

from libcpp cimport bool

from bnbpy.cython.node cimport Node


cdef class BaseNodeManager:

    cdef readonly:
        object bound_memory
        double lb
        set[Node] bound_nodes
        int nodecount

    cdef void memorize(self, Node node)

    cdef void forget(self, Node node)

    cdef void filter_memory_lb(self, double max_lb)

    cdef void clear_memory(self)

    cpdef bool not_empty(self)

    cpdef int size(self)

    cpdef void _enqueue(self, Node node)

    cpdef Node _dequeue(self)

    cpdef void _filter_by_lb(self, double max_lb)

    cpdef void _clear(self)

    cpdef void enqueue(self, Node node)

    cpdef void enqueue_all(self, list[Node] nodes)

    cpdef Node dequeue(self)

    cpdef Node get_lower_bound(self)

    cpdef void clear(self)

    cpdef void filter_by_lb(self, double max_lb)


cdef class LifoManager(BaseNodeManager):

    cdef:
        list[Node] stack

    cpdef void _enqueue(self, Node node)

    cpdef Node _dequeue(self)

    cpdef void _clear(self)

    cpdef void _filter_by_lb(self, double max_lb)


cdef class FifoManager(LifoManager):

    cpdef Node _dequeue(self)
