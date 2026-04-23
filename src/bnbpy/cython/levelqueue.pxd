# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

from libc.math cimport INFINITY
from libcpp cimport bool

from bnbpy.cython.manager cimport BaseNodeManager
from bnbpy.cython.node cimport Node
from bnbpy.cython.nodequeue cimport BestFirstSearch, PriorityManagerInterface


cdef class LevelQueue:
    """A single level in a level-based node manager.

    Internally holds a :class:`~bnbpy.cython.nodequeue.PriorityManagerInterface`
    for nodes at this level and maintains doubly-linked pointers to
    neighbouring levels.
    """

    cdef public:
        int level
        LevelQueue next
        LevelQueue prev

    cdef:
        PriorityManagerInterface queue

    cpdef int size(self)

    cpdef void set_queue(self, PriorityManagerInterface queue)

    cpdef void add_node(self, Node node)

    cpdef Node pop_node(self)

    cpdef void filter(self, double max_lb)

    cpdef double peek_lb(self)

    cdef inline Node get_lower_bound(self):
        if self.queue.not_empty():
            return self.queue.get_lower_bound()
        return None

    cdef inline set[Node] get_bound_nodes(self):
        return self.queue.get_bound_nodes()

    cdef list[Node] pop_all(self)


cdef class LevelManagerInterface(BaseNodeManager):
    """Abstract base class for level-based node managers.

    Nodes are bucketed by tree level in doubly-linked :class:`LevelQueue`
    objects.  Concrete subclasses must override :meth:`new_level` to supply
    the per-level priority queue.
    """

    cdef public:
        list[LevelQueue] levels
        LevelQueue current_level
        LevelQueue start_level
        LevelQueue last_level
        int node_counter
        int max_size
        bool use_fallback
        bool permanent_fallback

    cdef:
        double lb
        set[Node] bound_nodes

    cpdef LevelQueue new_level(self, int level)

    cdef void add_level(self)

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


cdef class CyclicBestSearch(LevelManagerInterface):
    """Cyclic best-first search node manager.

    Cycles through levels in round-robin order, dequeuing the best node
    within each level.  Falls back to a DFS-like (deepest-level-first)
    strategy when the queue exceeds *max_size* nodes.
    """

    cpdef LevelQueue new_level(self, int level)


cdef class DfsPriority(LevelManagerInterface):
    """Depth-first priority node manager.

    Always dequeues from the deepest non-empty level, picking the best
    node (lowest lb) within that level.  Equivalent to
    :class:`CyclicBestSearch` with permanent fallback enabled from the start.
    """

    cpdef LevelQueue new_level(self, int level)
