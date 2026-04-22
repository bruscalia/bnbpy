# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

from libcpp cimport bool

from bnbpy.cython.node cimport Node


cdef class BaseNodeManager:

    cpdef bool not_empty(self)

    cpdef int size(self)

    cpdef void enqueue(self, Node node)

    cpdef void enqueue_all(self, list[Node] nodes)

    cpdef Node dequeue(self)

    cpdef Node get_lower_bound(self)

    cpdef Node pop_lower_bound(self)

    cpdef void clear(self)

    cpdef void filter_by_lb(self, double max_lb)

    cpdef list[Node] pop_all(self)


cdef class LifoManager(BaseNodeManager):

    cdef:
        list[Node] stack
        double lb

    cpdef bool not_empty(self)

    cpdef int size(self)

    cpdef void enqueue(self, Node node)

    cpdef Node dequeue(self)

    cpdef Node get_lower_bound(self)

    cpdef Node pop_lower_bound(self)

    cpdef void clear(self)

    cpdef void filter_by_lb(self, double max_lb)


cdef class FifoManager(LifoManager):

    cpdef Node dequeue(self)
