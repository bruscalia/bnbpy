# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

from cpython.ref cimport PyObject
from libc.math cimport INFINITY
from libcpp cimport bool
from libcpp.vector cimport vector

from bnbpy.cython.manager cimport BaseNodeManager
from bnbpy.cython.node cimport Node
from bnbpy.cython.nodequeue cimport (
    NodePriEntry,
    NodePriQueue,
    PriorityManagerInterface,
)


# ---------------------------------------------------------------------------
# Raw CPython DECREF — accepts PyObject* directly
# ---------------------------------------------------------------------------
cdef extern from "Python.h":
    void _Py_DECREF "Py_DECREF"(PyObject* o)


# ---------------------------------------------------------------------------
# PriorityManagerInterface
# ---------------------------------------------------------------------------

cdef class PriorityManagerInterface(BaseNodeManager):
    """Priority queue manager backed by a native C++ binary heap.

    Stores nodes with ``vector[double]`` priorities; the queue behaves as a
    *min*-heap (smallest priority dequeued first).

    Reference counting contract
    ---------------------------
    * push  — C++ calls ``Py_INCREF`` on obj.
    * pop / pop_min_bound — ownership is *transferred* to the caller;
      Cython must:
        1. Cast ``entry.obj`` to ``Node`` (Cython auto-INCREFs).
        2. ``Py_DECREF(entry.obj)`` — release the push INCREF.
    * min_bound_entry — returns a *borrowed* copy (heap still owns).
      Cython auto-INCREFs on the cast; no explicit DECREF needed.
    * clear / filter_by_lb — C++ and/or Cython call ``Py_DECREF`` for
      every discarded entry.
    """

    def __cinit__(self):
        self.lb = INFINITY
        self.enqueue_time = 0.0
        self.dequeue_time = 0.0
        self.bound_nodes = set()

    def __dealloc__(self):
        self.pq.clear()

    cpdef int size(self):
        return <int>self.pq.size()

    cpdef bool not_empty(self):
        return not self.pq.empty()

    cpdef void enqueue(self, Node node):
        cdef vector[double] priority
        self.pq.push(<PyObject*>node, node.lb, self.make_priority(node))
        self.enqueue_bound_update(node)

    cpdef void enqueue_all(self, list[Node] nodes):
        cdef Node node
        for node in nodes:
            self.enqueue(node)

    cpdef Node dequeue(self):
        cdef:
            NodePriEntry entry
            Node node

        if self.pq.empty():
            return None
        entry = self.pq.pop()
        node = <Node>entry.obj
        _Py_DECREF(entry.obj)
        self.dequeue_bound_update(node)
        return node

    cpdef Node get_lower_bound(self):
        """Return the node with the smallest lb without removing it.

        Fast path: returns a node from the cached ``bound_nodes`` set in O(1).
        Slow path: scans the entire C++ heap to find all nodes tied at the
        minimum lb, rebuilds ``bound_nodes``, and updates ``self.lb``.
        """
        cdef:
            vector[NodePriEntry] candidates
            Node node
            size_t i

        if self.pq.empty():
            return None

        for node in self.bound_nodes:
            return node

        self.bound_nodes.clear()
        self.lb = self.pq.fill_min_lb_nodes(candidates)
        for i in range(candidates.size()):
            node = <Node>candidates[i].obj
            self.bound_nodes.add(node)

        for node in self.bound_nodes:
            return node
        return None

    cpdef Node pop_lower_bound(self):
        """Remove and return the node with the smallest lb."""
        cdef:
            NodePriEntry entry
            Node node

        if self.pq.empty():
            return None
        entry = self.pq.pop_min_bound()
        node = <Node>entry.obj
        _Py_DECREF(entry.obj)
        self.dequeue_bound_update(node)
        return node

    cpdef void filter_by_lb(self, double max_lb):
        """Keep only nodes whose lb < *max_lb*; call cleanup() on the rest."""
        cdef:
            vector[NodePriEntry] removed
            NodePriEntry entry
            Node node
            size_t i

        removed = self.pq.filter(max_lb)
        for i in range(removed.size()):
            entry = removed[i]
            node = <Node>entry.obj
            _Py_DECREF(entry.obj)
            node.cleanup()

        if self.pq.empty():
            self.lb = INFINITY
            self.bound_nodes.clear()

    cpdef void clear(self):
        self.pq.clear()
        self.lb = INFINITY
        self.bound_nodes.clear()

    cpdef list[Node] pop_all(self):
        cdef:
            NodePriEntry entry
            Node node
            list nodes = []

        while not self.pq.empty():
            entry = self.pq.pop()
            node = <Node>entry.obj
            _Py_DECREF(entry.obj)
            nodes.append(node)
        self.lb = INFINITY
        self.bound_nodes.clear()
        return nodes

    cpdef void reset_timers(self):
        """Reset enqueue_time and dequeue_time accumulators to zero."""
        self.enqueue_time = 0.0
        self.dequeue_time = 0.0

    cpdef double peek_lb(self):
        return self.lb

    cpdef set[Node] get_bound_nodes(self):
        return self.bound_nodes

    cpdef vector[double] make_priority(self, Node node):
        raise NotImplementedError("Subclasses must implement make_priority()")


# ---------------------------------------------------------------------------
# Concrete strategy subclass
# ---------------------------------------------------------------------------

cdef class BestFirstSearch(PriorityManagerInterface):
    """Best-first ordering: ``(lb, -level, -index)``."""

    cpdef vector[double] make_priority(self, Node node):
        return [node.lb, -node.level, -node.get_index()]
