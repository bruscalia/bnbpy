# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

cimport cython
from cpython.ref cimport PyObject
from libcpp.vector cimport vector

from bnbpy.cython.node cimport Node
from bnbpy.cython.nodequeue cimport (
    NodePriEntry,
    NodePriQueue,
)


# ---------------------------------------------------------------------------
# Raw CPython DECREF — accepts PyObject* directly
# ---------------------------------------------------------------------------
cdef extern from "Python.h":
    void _Py_DECREF "Py_DECREF"(PyObject* o)

# ---------------------------------------------------------------------------
# NodePriQueueWrapper
# ---------------------------------------------------------------------------

@cython.final
cdef class NodePriQueueWrapper:
    """Min-heap of nodes with ``vector[double]`` priorities, backed by a
    native C++ binary heap (lexicographic order; smallest first).

    Low-level building block of :class:`PriorityManagerTemplate` and
    :class:`LevelQueue`. It does not track lower bounds by itself.
    """

    def __dealloc__(self):
        self.pq.clear()

    @cython.final
    cpdef void push(self, Node node, vector[double]& priority):
        """Insert *node* with the given priority vector."""
        self.pq.push(<PyObject*>node, node.lb, priority)

    @cython.final
    cpdef Node pop(self):
        """Remove and return the node with the smallest priority,
        or ``None`` if empty."""
        cdef:
            NodePriEntry entry
            Node node

        if self.pq.empty():
            return None
        entry = self.pq.pop()
        node = <Node>entry.obj
        _Py_DECREF(entry.obj)
        return node

    @cython.final
    cpdef size_t size(self):
        """Number of nodes in the heap."""
        return self.pq.size()

    @cython.final
    cpdef void filter(self, double max_lb):
        """Remove the nodes with ``lb >= max_lb`` (lower bound at
        insertion) and mark them as fathomed."""
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
            node.fathom()

    @cython.final
    cpdef void clear(self):
        """Remove all nodes."""
        self.pq.clear()
