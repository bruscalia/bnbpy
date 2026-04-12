# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from collections import deque

from bnbpy.cython.node cimport Node


cdef class BaseNodeManager:

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

    def __cinit__(self):
        self.stack = deque()

    cpdef bool not_empty(self):
        return len(self.stack) > 0

    cpdef int size(self):
        return len(self.stack)

    cpdef void enqueue(self, Node node):
        self.stack.append(node)

    cpdef Node dequeue(self):
        if self.not_empty():
            return self.stack.pop()
        return None

    cpdef Node get_lower_bound(self):
        if self.not_empty():
            return min(self.stack, key=get_node_lb)
        return None

    cpdef Node pop_lower_bound(self):
        if self.not_empty():
            min_node = min(self.stack, key=get_node_lb)
            self.stack.remove(min_node)
            return min_node
        return None

    cpdef void clear(self):
        self.stack.clear()

    cpdef void filter_by_lb(self, double max_lb):
        self.stack = deque([node for node in self.stack if node.lb <= max_lb])

    cpdef list[Node] pop_all(self):
        nodes = list(self.stack)
        self.stack.clear()
        return nodes


cdef class FifoManager(LifoManager):

    cpdef Node dequeue(self):
        if self.not_empty():
            return self.stack.popleft()
        return None
