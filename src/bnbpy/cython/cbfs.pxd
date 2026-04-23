# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

from libc.math cimport INFINITY
from libcpp cimport bool

from bnbpy.cython.manager cimport BaseNodeManager
from bnbpy.cython.node cimport Node
from bnbpy.cython.priqueue_cpp cimport BestCppPriQueue, DfsCppPriQueue, CppPriorityQueue


cdef class CycleLevel:
    cdef public:
        int level
        CycleLevel next
        CycleLevel prev

    cdef:
        CppPriorityQueue pri_queue

    cpdef int size(self)

    cpdef void set_queue(self, CppPriorityQueue pri_queue)

    cpdef void add_node(self, Node node)

    cpdef Node pop_node(self)

    cpdef void filter(self, double max_lb)

    cpdef double peek_lb(self)

    cdef inline Node get_lower_bound(self):
        if self.pri_queue.not_empty():
            return self.pri_queue.get_lower_bound()
        return None

    cdef inline set[Node] get_bound_nodes(self):
        return self.pri_queue.get_bound_nodes()

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
        bool permanent_fallback

    cdef:
        double lb
        set[Node] bound_nodes

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

    cdef inline void enqueue_bound_update(self, Node node):
        if node.lb <= self.lb:
            if node.lb < self.lb:
                self.lb = node.lb
                self.bound_nodes.clear()
            self.bound_nodes.add(node)

    cdef inline void dequeue_bound_update(self, Node node):
        if node.lb <= self.lb:
            self.bound_nodes.discard(node)
