# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

from collections import defaultdict
from libc.math cimport INFINITY
from libcpp cimport bool
from libcpp.vector cimport vector

from bnbpy.cython.node cimport Node
from bnbpy.cython.problem cimport Problem


cdef class BaseNodeManager:
    """Base class for managing active nodes in a Branch & Bound search.

    This class implements the *Template Method* pattern.  Subclasses
    **must** implement the four abstract hooks:

    *   ``_enqueue`` — add a node to the underlying data structure.
    *   ``_dequeue`` — remove and return the next node.
    *   ``_filter_by_lb`` — physically discard nodes with lb >= max_lb.
    *   ``_clear`` — empty the underlying data structure.

    All other public methods (``enqueue``, ``dequeue``, ``size``,
    ``not_empty``, ``filter_by_lb``, ``clear``, ``get_lower_bound``,
    ``memorize``, ``forget``, ``filter_memory_lb``, ``clear_memory``,
    ``enqueue_all``) implement the template logic and should not be
    overridden.
    """

    def __cinit__(self, *args, **kwargs):
        self.bound_memory = defaultdict(set)
        self.lb = INFINITY
        self.bound_nodes = set()
        self.nodecount = 0

    @classmethod
    def __class_getitem__(cls, item: type[Problem]):
        """Support generic syntax BaseNodeManager[P] at runtime."""
        if not issubclass(item, Problem):
            raise TypeError(
                "BaseNodeManager can only be parameterized"
                f" with a Problem subclass, got {item}"
            )
        return cls

    cdef void memorize(self, Node node):
        """Record *node* in ``bound_memory`` and update ``lb`` / ``bound_nodes``."""
        self.bound_memory[node.lb].add(node)

        if node.lb < self.lb:
            self.lb = node.lb
            self.bound_nodes = self.bound_memory[node.lb]

    cdef void forget(self, Node node):
        """Remove *node* from ``bound_memory``; recompute ``lb`` if needed."""
        cdef:
            set[Node] s

        s = self.bound_memory[node.lb]
        s.discard(node)
        if not s:
            del self.bound_memory[node.lb]

    cdef void filter_memory_lb(self, double max_lb):
        """Remove all ``bound_memory`` entries with key >= *max_lb*."""
        cdef:
            vector[double] keys_to_remove
            double lb_key
            double min_key
            int i, n
            set[Node] s

        min_key = INFINITY
        keys_to_remove = vector[double]()
        keys_to_remove.reserve(len(self.bound_memory))
        for lb_key in self.bound_memory:
            if lb_key < min_key:
                min_key = lb_key
            if lb_key >= max_lb:
                keys_to_remove.push_back(lb_key)

        for i in range(keys_to_remove.size()):
            del self.bound_memory[keys_to_remove[i]]

        if min_key < max_lb:
            self.lb = min_key
            self.bound_nodes = self.bound_memory[min_key]
        else:
            self.lb = INFINITY
            self.bound_nodes = set()

        n = 0
        for s in self.bound_memory.values():
            n += len(s)
        self.nodecount = n

    cdef void clear_memory(self):
        """Reset ``bound_memory``, ``lb``, and ``bound_nodes``."""
        self.bound_memory.clear()
        self.lb = INFINITY
        self.bound_nodes = set()

    cpdef int size(self):
        """Returns the number of nodes in the manager.

        Returns
        -------
        int
            The number of nodes in the manager.
        """
        return self.nodecount

    cpdef bool not_empty(self):
        """Checks if the manager is not empty.

        Returns
        -------
        bool
            True if the manager is not empty, False otherwise.
        """
        return self.nodecount > 0

    cpdef void _enqueue(self, Node node):
        """Internal hook — add *node* to the underlying structure.

        Must be implemented by subclasses.
        """
        raise NotImplementedError("Must implement _enqueue()")

    cpdef Node _dequeue(self):
        """Internal hook — remove and return the next node.

        Must be implemented by subclasses.
        """
        raise NotImplementedError("Must implement _dequeue()")

    cpdef void _filter_by_lb(self, double max_lb):
        """Internal hook — physically remove nodes with lb >= *max_lb*.

        Default is a no-op.  Override in subclasses for correct pruning.
        """
        pass

    cpdef void _clear(self):
        """Internal hook — empty the underlying data structure.

        Must be implemented by subclasses.
        """
        raise NotImplementedError("Must implement _clear()")

    cpdef void enqueue(self, Node node):
        """Adds a node to the manager and records it in ``bound_memory``.

        Parameters
        ----------
        node : Node
            The node to add.
        """
        self._enqueue(node)
        self.memorize(node)
        self.nodecount += 1

    cpdef void enqueue_all(self, list[Node] nodes):
        """Adds a list of nodes to the manager.

        Parameters
        ----------
        nodes : list[Node]
            The list of nodes to add.
        """
        cdef:
            Node node
        for node in nodes:
            self.enqueue(node)

    cpdef Node dequeue(self):
        """Removes and returns the next node, updating ``bound_memory``.

        Returns
        -------
        Node
            The next node, or ``None`` if empty.
        """
        cdef:
            Node node
        node = self._dequeue()
        if node is not None:
            self.forget(node)
            self.nodecount -= 1
        return node

    cpdef Node get_lower_bound(self):
        """Gets a node with the global minimum lower bound without removing it.

        Returns
        -------
        Node
            A node with the lowest lower bound, or ``None`` if empty.
        """
        cdef:
            Node node

        # If bound notes are updated
        for node in self.bound_nodes:
            return node
        # Clear out any stale bound_memory entries
        # and update lb / bound_nodes accordingly
        self.filter_memory_lb(INFINITY)
        for node in self.bound_nodes:
            return node
        # Last resort: no bound nodes, so return None
        return None

    cpdef void clear(self):
        """Makes the manager empty."""
        self._clear()
        self.clear_memory()
        self.nodecount = 0

    cpdef void filter_by_lb(self, double max_lb):
        """Remove nodes with lb >= *max_lb* and update ``bound_memory``.

        Parameters
        ----------
        max_lb : float
            The maximum lower bound value (exclusive upper bound).
        """
        cdef:
            int n
            set[Node] s

        self._filter_by_lb(max_lb)
        self.filter_memory_lb(max_lb)


cdef class LifoManager(BaseNodeManager):
    """Last-In First-Out (stack) node manager.

    :meth:`dequeue` returns the most recently enqueued node.
    :meth:`get_lower_bound` returns a node with the minimum ``lb`` in O(1)
    via the inherited ``bound_memory`` mechanism.
    """

    def __cinit__(self, *args, **kwargs):
        self.stack = []

    cpdef void _enqueue(self, Node node):
        self.stack.append(node)

    cpdef Node _dequeue(self):
        if self.nodecount > 0:
            return self.stack.pop()
        return None

    cpdef void _clear(self):
        self.stack.clear()

    cpdef void _filter_by_lb(self, double max_lb):
        cdef:
            int i, j
            Node node

        j = 0
        for i in range(len(self.stack)):
            node = self.stack[i]
            if node.lb < max_lb:
                self.stack[j] = node
                j += 1
            else:
                node.cleanup()
        self.stack = self.stack[:j]


cdef class FifoManager(LifoManager):
    """First-In First-Out (queue) node manager.

    Identical to :class:`LifoManager` except that :meth:`dequeue` returns
    the **oldest** enqueued node (``pop(0)``).
    """

    cpdef Node _dequeue(self):
        if self.nodecount > 0:
            return self.stack.pop(0)
        return None
