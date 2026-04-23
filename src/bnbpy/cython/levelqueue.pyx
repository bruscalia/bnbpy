# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

import logging

from libc.math cimport INFINITY
from libcpp cimport bool

from bnbpy.cython.manager cimport BaseNodeManager
from bnbpy.cython.node cimport Node
from bnbpy.cython.nodequeue cimport BestFirstSearch, PriorityManagerInterface

log = logging.getLogger(__name__)


cdef:
    double HIGH_POS = INFINITY


# ---------------------------------------------------------------------------
# LevelQueue
# ---------------------------------------------------------------------------

cdef class LevelQueue:
    """A single level in a level-based node manager.

    Internally holds a :class:`~bnbpy.cython.nodequeue.PriorityManagerInterface`
    for nodes at this level and maintains doubly-linked pointers to
    neighbouring levels.
    """

    @classmethod
    def __class_getitem__(cls, item):
        """Support generic syntax LevelQueue[P] at runtime."""
        return cls

    def __init__(self, int level):
        self.level = level
        self.next = self
        self.prev = self
        self.queue = BestFirstSearch()

    cpdef int size(self):
        return self.queue.size()

    cpdef void set_queue(self, PriorityManagerInterface queue):
        self.queue = queue

    cpdef void add_node(self, Node node):
        self.queue.enqueue(node)

    cpdef Node pop_node(self):
        return self.queue.dequeue()

    cpdef void filter(self, double max_lb):
        self.queue.filter_by_lb(max_lb)

    cpdef double peek_lb(self):
        return self.queue.peek_lb()

    cdef list[Node] pop_all(self):
        return self.queue.pop_all()


# ---------------------------------------------------------------------------
# LevelManagerInterface
# ---------------------------------------------------------------------------

cdef class LevelManagerInterface(BaseNodeManager):
    """Abstract base for level-based node managers.

    Nodes are bucketed by tree level into doubly-linked :class:`LevelQueue`
    objects.  Concrete subclasses must override :meth:`new_level` to control
    which :class:`~bnbpy.cython.nodequeue.PriorityManagerInterface` is used
    at each level.
    """

    def __init__(self, int max_size=100_000, bool permanent_fallback=False):
        self.levels = []
        self.current_level = None
        self.start_level = None
        self.last_level = None
        self.node_counter = 0
        self.max_size = max_size
        self.use_fallback = False
        self.permanent_fallback = permanent_fallback
        self.add_level()
        self.lb = HIGH_POS
        self.bound_nodes = set()

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

    cpdef int size(self):
        return self.node_counter

    cpdef bool not_empty(self):
        return self.node_counter > 0

    cpdef void enqueue(self, Node node):
        cdef int i

        if not self.use_fallback and self.node_counter > self.max_size:
            self.enter_fallback()

        if node.level > self.last_level.level:
            for i in range(node.level - self.last_level.level):
                self.add_level()

        self.levels[node.level].add_node(node)
        self.node_counter += 1
        self.enqueue_bound_update(node)

        if self.use_fallback and node.level > self.current_level.level:
            self.current_level = self.levels[node.level]

    cpdef void enqueue_all(self, list[Node] nodes):
        cdef Node node
        for node in nodes:
            self.enqueue(node)

    cpdef Node dequeue(self):
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
            node = self.current_level.pop_node()
            self.dequeue_bound_update(node)
            self.node_counter -= 1
            if (
                not self.permanent_fallback
                and self.node_counter <= self.max_size // 2
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

        self.node_counter -= 1
        node = self.current_level.pop_node()
        self.dequeue_bound_update(node)
        return node

    cpdef Node get_lower_bound(self):
        cdef:
            Node node
            Node min_node
            set[Node] bound_nodes
            LevelQueue level
            double min_lb

        # Fast path: cached bound_nodes is populated
        for node in self.bound_nodes:
            return node

        min_lb = HIGH_POS
        min_node = None
        self.bound_nodes.clear()
        for level in self.levels:
            if level.size() == 0 or level.peek_lb() > min_lb:
                continue
            node = level.get_lower_bound()
            if node is None:
                continue
            if node.lb <= min_lb:
                bound_nodes = level.get_bound_nodes()
                if node.lb < min_lb:
                    min_lb = node.lb
                    min_node = node
                    self.bound_nodes.clear()
                    self.bound_nodes.update(bound_nodes)
                else:
                    self.bound_nodes.update(bound_nodes)

        self.lb = min_lb
        return min_node

    cpdef Node pop_lower_bound(self):
        """Remove and return the node with the smallest lb."""
        cdef:
            Node node
            Node min_node
            LevelQueue best_level
            LevelQueue level
            double min_lb

        if self.node_counter == 0:
            return None

        min_lb = HIGH_POS
        best_level = None
        for level in self.levels:
            if level.size() == 0:
                continue
            if level.peek_lb() < min_lb:
                min_lb = level.peek_lb()
                best_level = level

        if best_level is None:
            return None

        node = best_level.queue.pop_lower_bound()
        if node is None:
            return None

        self.node_counter -= 1
        self.dequeue_bound_update(node)

        if self.node_counter == 0:
            self.lb = HIGH_POS
            self.bound_nodes.clear()

        return node

    cpdef void filter_by_lb(self, double max_lb):
        cdef:
            LevelQueue level
            int node_counter

        node_counter = 0
        for level in self.levels:
            level.filter(max_lb)
            node_counter += level.size()

        self.node_counter = node_counter
        if self.node_counter == 0:
            self.lb = HIGH_POS
            self.bound_nodes.clear()

    cpdef void clear(self):
        self.levels = []
        self.current_level = None
        self.start_level = None
        self.last_level = None
        self.node_counter = 0
        self.use_fallback = False
        self.add_level()
        self.lb = HIGH_POS
        self.bound_nodes.clear()

    cpdef list[Node] pop_all(self):
        cdef:
            LevelQueue level
            list[Node] nodes = []

        for level in self.levels:
            nodes.extend(level.pop_all())
        self.node_counter = 0
        self.lb = HIGH_POS
        self.bound_nodes.clear()
        return nodes

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
        cdef LevelQueue lvl = LevelQueue(level)
        lvl.set_queue(BestFirstSearch())
        return lvl


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
        cdef LevelQueue lvl = LevelQueue(level)
        lvl.set_queue(BestFirstSearch())
        return lvl
