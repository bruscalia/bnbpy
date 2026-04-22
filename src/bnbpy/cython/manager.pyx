# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

from libc.math cimport INFINITY
from libcpp cimport bool
from collections import deque

from bnbpy.cython.node cimport Node
from bnbpy.cython.problem cimport Problem


cdef class BaseNodeManager:
    """Base class for managing active nodes in a Branch & Bound search.

    Note that due to Cython limitations this class is not implemented as an
    ABC, but subclasses **must** implement:

    *   ``size``
    *   ``not_empty``
    *   ``enqueue``
    *   ``dequeue``
    *   ``get_lower_bound``
    *   ``pop_lower_bound``
    *   ``clear``
    *   ``pop_all``

    ``enqueue_all`` and ``filter_by_lb`` have default implementations that
    may be overridden for better performance.
    """

    @classmethod
    def __class_getitem__(cls, item: type[Problem]):
        """Support generic syntax BaseNodeManager[P] at runtime."""
        if not issubclass(item, Problem):
            raise TypeError(
                "BaseNodeManager can only be parameterized"
                f" with a Problem subclass, got {item}"
            )
        return cls

    cpdef int size(self):
        """Returns the number of nodes in the manager.

        Returns
        -------
        int
            The number of nodes in the manager.
        """
        raise NotImplementedError("Must implement size()")

    cpdef bool not_empty(self):
        """Checks if the priority queue is not empty.

        Returns
        -------
        bool
            True if the queue is not empty, False otherwise.
        """
        raise NotImplementedError("Must implement not_empty()")

    cpdef void enqueue(self, Node node):
        """Adds a node to the priority queue.

        Parameters
        ----------
        node : Node
            The node to add to the queue.
        """
        raise NotImplementedError("Must implement enqueue()")

    cpdef void enqueue_all(self, list[Node] nodes):
        """Adds a list of nodes to the queue.
        Might be overridden in subclasses for better performance.

        Parameters
        ----------
        nodes : list[Node]
            The list of nodes to add to the queue.
        """
        for node in nodes:
            self.enqueue(node)

    cpdef Node dequeue(self):
        """Removes and returns the next evaluated node.

        Returns
        -------
        Node
            The next evaluated node.
        """
        raise NotImplementedError("Must implement dequeue()")

    cpdef Node get_lower_bound(self):
        """Gets the node of lower bound but
        does not remove it from the queue.

        Returns
        -------
        Node
            The node with the lowest lower bound.
        """
        raise NotImplementedError("Must implement get_lower_bound()")

    cpdef Node pop_lower_bound(self):
        """Removes and returns the node of lower bound.

        Returns
        -------
        Node
            The node with the lowest lower bound.
        """
        raise NotImplementedError("Must implement pop_lower_bound()")

    cpdef void clear(self):
        """Makes queue empty."""
        raise NotImplementedError("Must implement clear()")

    cpdef void filter_by_lb(self, double max_lb):
        """Filter nodes by lower bound.
        This method is not implemented in the base class,
        but can be overridden in subclasses.

        Parameters
        ----------
        max_lb : float
            The maximum lower bound value.
        """
        # Not implemented, but won't be strictly necessary
        pass

    cpdef list[Node] pop_all(self):
        """Removes and returns all nodes in the manager.

        Returns
        -------
        list[Node]
            A list of all nodes in the manager.
        """
        raise NotImplementedError("Must implement pop_all()")


cpdef double get_node_lb(Node node):
    return node.lb


cdef class LifoManager(BaseNodeManager):
    """Last-In First-Out (stack) node manager.

    :meth:`dequeue` returns the most recently enqueued node.
    :meth:`get_lower_bound` and :meth:`pop_lower_bound` perform a linear
    scan over the stack to find the node with minimum ``lb``.
    """

    def __cinit__(self):
        self.stack = []
        self.lb = INFINITY

    cpdef bool not_empty(self):
        return len(self.stack) > 0

    cpdef int size(self):
        return len(self.stack)

    cpdef void enqueue(self, Node node):
        if node.lb < self.lb:
            self.lb = node.lb
        self.stack.append(node)

    cpdef Node dequeue(self):
        if self.not_empty():
            return self.stack.pop()
        return None

    cpdef Node get_lower_bound(self):
        cdef:
            Node node, min_node
        if self.not_empty():
            min_node = self.stack[0]
            for node in self.stack:
                if node.lb <= self.lb:
                    return node
                if node.lb < min_node.lb:
                    min_node = node
            self.lb = min_node.lb
            return min_node
        return None

    cpdef Node pop_lower_bound(self):
        if self.not_empty():
            min_node = self.get_lower_bound()
            self.stack.remove(min_node)
            return min_node
        return None

    cpdef void clear(self):
        self.stack.clear()
        self.lb = INFINITY

    cpdef void filter_by_lb(self, double max_lb):
        cdef:
            int i, j, N
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

    cpdef list[Node] pop_all(self):
        nodes = list(self.stack)
        self.stack.clear()
        return nodes


cdef class FifoManager(LifoManager):
    """First-In First-Out (queue) node manager.

    Identical to :class:`LifoManager` except that :meth:`dequeue` returns
    the **oldest** enqueued node (``popleft``).
    """

    cpdef Node dequeue(self):
        if self.not_empty():
            return self.stack.pop(0)
        return None
