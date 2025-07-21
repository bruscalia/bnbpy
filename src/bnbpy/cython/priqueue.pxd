# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from bnbpy.cython.node cimport Node


cdef class NodePriQueue:
    cdef public:
        tuple priority
        Node node


cdef inline NodePriQueue init_node_pri_queue(tuple priority, Node node):

    cdef:
        NodePriQueue npri
    npri = NodePriQueue.__new__(NodePriQueue)
    npri.priority = priority
    npri.node = node
    return npri


cdef class BasePriQueue:

    cpdef bint not_empty(BasePriQueue self)

    cpdef void enqueue(BasePriQueue self, Node node)

    cpdef Node dequeue(BasePriQueue self)

    cpdef Node get_lower_bound(BasePriQueue self)

    cpdef Node pop_lower_bound(BasePriQueue self)

    cpdef void clear(BasePriQueue self)

    cpdef void filter_by_lb(BasePriQueue self, double max_lb)


cdef class HeapPriQueue(BasePriQueue):

    cdef public:
        list[NodePriQueue] _queue

    cpdef bint not_empty(HeapPriQueue self)

    cpdef Node dequeue(HeapPriQueue self)

    cpdef Node get_lower_bound(HeapPriQueue self)

    cpdef Node pop_lower_bound(HeapPriQueue self)

    cpdef void filter_by_lb(HeapPriQueue self, double max_lb)

    cpdef void clear(HeapPriQueue self)


cdef class DFSPriQueue(HeapPriQueue):

    cpdef void enqueue(DFSPriQueue self, Node node)


cdef class BFSPriQueue(HeapPriQueue):

    cpdef void enqueue(BFSPriQueue self, Node node)


cdef class BestPriQueue(HeapPriQueue):

    cpdef void enqueue(BestPriQueue self, Node node)

