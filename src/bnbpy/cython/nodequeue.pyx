# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

cimport cython
from cpython.ref cimport PyObject
from libcpp cimport bool
from libcpp.vector cimport vector

from bnbpy.cython.manager cimport BaseNodeManager
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

    def __dealloc__(self):
        self.pq.clear()

    @cython.final
    cpdef void push(self, Node node, vector[double]& priority):
        self.pq.push(<PyObject*>node, node.lb, priority)

    @cython.final
    cpdef Node pop(self):
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
        return self.pq.size()

    @cython.final
    cpdef void filter(self, double max_lb):
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

    @cython.final
    cpdef void clear(self):
        self.pq.clear()
