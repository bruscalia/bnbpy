# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

from libcpp cimport bool
from libcpp.vector cimport vector

from bnbpy.cython.manager cimport BaseNodeManager
from bnbpy.cython.node cimport Node
from bnbpy.cython.nodequeue cimport NodePriQueueWrapper


cdef class LevelQueue:

    cdef public:
        LevelQueue next
        LevelQueue prev

    cdef readonly:
        int level
        NodePriQueueWrapper pq

    cpdef int size(self)

    cpdef void push(self, Node node)

    cpdef Node pop(self)

    cpdef void filter(self, double max_lb)

    cpdef vector[double] make_priority(self, Node node)


cdef class LevelManagerInterface(BaseNodeManager):
    """Abstract base class for level-based node managers.

    Nodes are bucketed by tree level.  Concrete subclasses must override
    :meth:`new_level` to define which :class:`LevelQueue` is used at
    each level.
    """

    cdef public:
        list[LevelQueue] levels
        LevelQueue current_level
        LevelQueue start_level
        LevelQueue last_level
        int max_size
        bool use_fallback
        bool permanent_fallback

    cpdef LevelQueue new_level(self, int level)

    cdef void add_level(self)

    cpdef void _enqueue(self, Node node)

    cpdef Node _dequeue(self)

    cpdef void _filter_by_lb(self, double max_lb)

    cpdef void _clear(self)

    cpdef void reset_level(self)

    cdef void enter_fallback(self)

    cdef void exit_fallback(self)


cdef class CyclicBestSearch(LevelManagerInterface):
    """Cyclic best-first search node manager.

    Cycles through tree levels in round-robin order, dequeuing the best
    (lowest-lb) node within each level.  Switches to deepest-level-first
    when the total node count exceeds *max_size*.
    """

    cpdef LevelQueue new_level(self, int level)


cdef class DfsPriority(LevelManagerInterface):
    """Depth-first priority node manager.

    Always dequeues the best node (lowest lb) from the deepest non-empty
    level.  Equivalent to :class:`CyclicBestSearch` with permanent fallback
    engaged from the start.
    """

    cpdef LevelQueue new_level(self, int level)
