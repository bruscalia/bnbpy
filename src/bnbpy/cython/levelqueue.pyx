# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

import logging

from libcpp cimport bool
from libcpp.vector cimport vector

from bnbpy.cython.manager cimport BaseNodeManager
from bnbpy.cython.node cimport Node
from bnbpy.cython.nodequeue cimport NodePriQueueWrapper

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LevelQueue
# ---------------------------------------------------------------------------

cdef class LevelQueue:
    """A single level in a level-based node manager.

    Internally holds a wrapper of a raw C++
    :class:`NodePriQueueWrapper`
    (min-heap) and maintains
    doubly-linked pointers to neighbouring levels.

    The ordering key for each node is produced by :meth:`make_priority`;
    subclasses override this to customise the intra-level priority.
    """

    @classmethod
    def __class_getitem__(cls, item):
        """Support generic syntax LevelQueue[P] at runtime."""
        return cls

    def __init__(self, int level):
        self.level = level
        self.next = self
        self.prev = self
        self.pq = NodePriQueueWrapper()

    def __dealloc__(self):
        if self.pq is not None:
            self.pq.clear()

    cpdef int size(self):
        return <int>self.pq.size()

    cpdef void push(self, Node node):
        self.pq.push(node, self.make_priority(node))
        # Possibly reactivating this level in forward checks
        # if self.pq.size() == 1:
        #     self.prev.next = self

    cpdef Node pop(self):
        # Bypass in forward direction
        # to avoid O(n) pointer updates when popping the last node
        # if self.pq.size() == 1:
        #     self.prev.next = self.next
        return self.pq.pop()

    cpdef void filter(self, double max_lb):
        self.pq.filter(max_lb)

    cpdef vector[double] make_priority(self, Node node):
        """Return the ordering key for *node* (smaller → dequeued first).

        Default is best-first: ``(lb, -level, -index)``.
        Override in subclasses to change intra-level ordering.

        Parameters
        ----------
        node : Node
            The node being enqueued.

        Returns
        -------
        list[float]
            Priority vector; smaller values are dequeued first.
        """
        cdef:
            vector[double] pri = vector[double](3)
        pri[0] = node.lb
        pri[1] = -node.level
        pri[2] = -node.get_index()
        return pri


# ---------------------------------------------------------------------------
# LevelManagerInterface
# ---------------------------------------------------------------------------

cdef class LevelManagerInterface(BaseNodeManager):
    """Abstract base for level-based node managers.

    Nodes are bucketed by tree level into doubly-linked :class:`LevelQueue`
    objects.  Concrete subclasses must override :meth:`new_level` to control
    which :class:`LevelQueue` subclass (and thus which priority) is used
    at each level.
    """

    def __init__(self, int max_size=100_000, bool permanent_fallback=False):
        self.levels = []
        self.current_level = None
        self.start_level = None
        self.last_level = None
        self.max_size = max_size
        self.use_fallback = False
        self.permanent_fallback = permanent_fallback
        self.add_level()

    cpdef LevelQueue new_level(self, int level):
        raise NotImplementedError("Subclasses must implement new_level()")

    cdef void add_level(self):
        cdef LevelQueue new_lv

        new_lv = self.new_level(len(self.levels))
        if not self.levels:
            self.levels.append(new_lv)
            self.current_level = new_lv
            self.start_level = new_lv
            self.last_level = new_lv
        else:
            self.last_level.next = new_lv
            new_lv.prev = self.last_level
            new_lv.next = self.start_level
            self.start_level.prev = new_lv
            self.levels.append(new_lv)
            self.last_level = new_lv

    cpdef void _enqueue(self, Node node):
        cdef int i

        if not self.use_fallback and self.nodecount > self.max_size:
            self.enter_fallback()

        if node.level > self.last_level.level:
            for i in range(node.level - self.last_level.level):
                self.add_level()

        self.levels[node.level].push(node)

        if self.use_fallback and node.level > self.current_level.level:
            self.current_level = self.levels[node.level]

    cpdef Node _dequeue(self):
        cdef:
            LevelQueue start
            Node node

        # Fallback: always dequeue from deepest non-empty level
        if self.use_fallback:
            start = self.current_level
            while self.current_level.size() == 0:
                self.current_level = self.current_level.prev
                if self.current_level is start:
                    return None
            node = self.current_level.pop()
            if (
                not self.permanent_fallback
                and self.nodecount - 1 <= self.max_size // 2
            ):
                self.exit_fallback()
            return node

        # Normal cycling: advance one level, wrap around if empty
        self.current_level = self.current_level.next
        if self.current_level.size() == 0:
            self.current_level = self.start_level

        start = self.current_level
        while self.current_level.size() == 0:
            self.current_level = self.current_level.next
            if self.current_level is start:
                return None

        node = self.current_level.pop()
        return node

    cpdef void _filter_by_lb(self, double max_lb):
        cdef LevelQueue level
        for level in self.levels:
            level.filter(max_lb)

    cpdef void _clear(self):
        cdef LevelQueue level
        for level in self.levels:
            level.pq.clear()
            level.next = None
            level.prev = None
        self.levels = []
        self.current_level = None
        self.start_level = None
        self.last_level = None
        self.use_fallback = False
        self.add_level()

    cpdef void reset_level(self):
        """Reset the current level pointer back to the first level."""
        self.current_level = self.start_level

    cdef void enter_fallback(self):
        cdef LevelQueue start

        self.use_fallback = True
        log.info("Entering fallback — level queues are full")

        start = self.last_level
        self.current_level = start
        while self.current_level.size() == 0:
            self.current_level = self.current_level.prev
            if self.current_level is start:
                break

    cdef void exit_fallback(self):
        log.info("Exiting fallback — resuming cyclic traversal")
        self.use_fallback = False


# ---------------------------------------------------------------------------
# CyclicBestSearch
# ---------------------------------------------------------------------------

cdef class CyclicBestSearch(LevelManagerInterface):
    """Cyclic best-first search.

    Cycles through tree levels in round-robin order, always dequeuing the
    lowest-lb node within the current level.  Switches to a DFS-like
    deepest-first strategy when the total node count exceeds *max_size*,
    and returns to cycling once the count falls to half of *max_size*
    (unless *permanent_fallback* is set).
    """

    def __init__(
        self,
        int max_size=100_000,
        bool permanent_fallback=False,
    ):
        super(CyclicBestSearch, self).__init__(max_size, permanent_fallback)

    cpdef LevelQueue new_level(self, int level):
        return LevelQueue(level)


# ---------------------------------------------------------------------------
# DfsPriority
# ---------------------------------------------------------------------------

cdef class DfsPriority(LevelManagerInterface):
    """Depth-first priority manager.

    Always dequeues the best node (lowest lb) from the deepest non-empty
    level, giving DFS order with best-first tie-breaking within a level.
    The fallback mode is engaged permanently from initialisation.
    """

    def __init__(self):
        super(DfsPriority, self).__init__(max_size=0, permanent_fallback=True)
        self.use_fallback = True

    cpdef LevelQueue new_level(self, int level):
        return LevelQueue(level)
