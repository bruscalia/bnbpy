# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

from cpython.ref cimport PyObject
from libc.math cimport INFINITY
from libcpp cimport bool
from libcpp.vector cimport vector

from bnbpy.cython.manager cimport BaseNodeManager
from bnbpy.cython.node cimport Node
from bnbpy.cython.priqueue_cpp cimport CppPriorityQueue, PriNode, PyPriQueue


# ---------------------------------------------------------------------------
# Raw CPython DECREF — accepts PyObject* directly to avoid type-coercion noise
# ---------------------------------------------------------------------------
cdef extern from "Python.h":
    void _Py_DECREF "Py_DECREF"(PyObject* o)


# ---------------------------------------------------------------------------
# Monotonic clock helper (nanosecond resolution, minimal overhead)
# ---------------------------------------------------------------------------
cdef extern from "time.h" nogil:
    struct timespec:
        long tv_sec
        long tv_nsec
    int clock_gettime(int clk_id, timespec* tp)
    int CLOCK_MONOTONIC


cdef inline double _now_ns():
    cdef timespec ts
    clock_gettime(CLOCK_MONOTONIC, &ts)
    return <double>ts.tv_sec * 1.0e9 + <double>ts.tv_nsec


# ---------------------------------------------------------------------------
# CppPriorityQueue
# ---------------------------------------------------------------------------

cdef class CppPriorityQueue(BaseNodeManager):
    """Priority queue backed by a native C++ binary heap with Python-object
    priorities.

    The C++ heap stores ``(PyObject* obj, double lb, PyObject* priority)``
    triples.  The comparator uses ``PyObject_RichCompareBool(..., Py_GT)``
    so the element with the *smallest* Python priority is dequeued first
    (min-heap semantics matching Python's :mod:`heapq`).

    Reference counting contract
    ---------------------------
    * push  — C++ calls ``Py_INCREF`` on both *obj* and *priority*.
    * pop / pop_min_bound — ownership is *transferred* to the caller;
      Cython receives a ``PriNode`` value copy whose pointers still carry
      the INCREF done on push.  Cython must:
        1. Cast ``entry.obj`` to ``Node`` (Cython auto-INCREFs).
        2. ``Py_DECREF(entry.obj)``      — release the push INCREF.
        3. ``Py_DECREF(entry.priority)`` — release the push INCREF.
    * min_bound_entry — returns a *borrowed* copy (heap still owns the
      original INCREF).  Cython auto-INCREFs on the cast; no explicit
      DECREF needed.
    * clear / filter_by_lb — C++ and/or Cython call ``Py_DECREF`` for
      every discarded entry.
    """

    def __cinit__(self):
        self.lb = INFINITY
        self.enqueue_time = 0.0
        self.dequeue_time = 0.0
        self.bound_nodes = set()

    def __dealloc__(self):
        # Release all PyObject references still inside the heap.
        self.pq.clear()

    cpdef int size(self):
        return <int>self.pq.size()

    cpdef bool not_empty(self):
        return not self.pq.empty()

    cpdef void enqueue(self, Node node):
        cdef:
            object priority
            double t0

        t0 = _now_ns()
        priority = self.make_priority(node)
        self.pq.push(<PyObject*>node, node.lb, <PyObject*>priority)
        # pq.push did Py_INCREF on both node and priority.
        # Our local 'priority' still holds one reference; when it goes out
        # of scope the refcount drops back to 1 (owned by the heap). Correct.
        self.enqueue_bound_update(node)
        self.enqueue_time += _now_ns() - t0

    cpdef void enqueue_all(self, list[Node] nodes):
        cdef Node node
        for node in nodes:
            self.enqueue(node)

    cpdef Node dequeue(self):
        cdef:
            PriNode entry
            Node node
            double t0

        if self.pq.empty():
            return None
        t0 = _now_ns()
        entry = self.pq.pop()           # transfers ownership
        node = <Node>entry.obj          # Cython INCREFs → refcount = 2
        _Py_DECREF(entry.obj)           # balance push INCREF → refcount = 1
        _Py_DECREF(entry.priority)      # release priority push INCREF
        self.dequeue_bound_update(node)
        self.dequeue_time += _now_ns() - t0
        return node

    cpdef Node get_lower_bound(self):
        """Return the node with the smallest lb without removing it.

        Fast path: returns a node from the cached ``bound_nodes`` set in O(1).
        Slow path: scans the entire C++ heap to find all nodes tied at the
        minimum lb, rebuilds ``bound_nodes``, and updates ``self.lb``.
        """
        cdef:
            vector[PriNode] candidates
            Node node
            size_t i

        if self.pq.empty():
            return None

        # Fast path: bound_nodes cache is populated.
        for node in self.bound_nodes:
            return node

        # Slow path: scan entire heap for all nodes tied at minimum lb.
        self.bound_nodes.clear()
        self.lb = self.pq.fill_min_lb_nodes(candidates)
        for i in range(candidates.size()):
            # Borrowed C++ ref; <Node> cast causes Cython to INCREF, giving
            # bound_nodes its own Python reference independent of the heap.
            node = <Node>candidates[i].obj
            self.bound_nodes.add(node)

        for node in self.bound_nodes:
            return node
        return None

    cpdef Node pop_lower_bound(self):
        """Remove and return the node with the smallest lb."""
        cdef:
            PriNode entry
            Node node

        if self.pq.empty():
            return None
        entry = self.pq.pop_min_bound()  # transfers ownership
        node = <Node>entry.obj           # Cython INCREFs → refcount = 2
        _Py_DECREF(entry.obj)            # balance push INCREF → refcount = 1
        _Py_DECREF(entry.priority)       # release priority push INCREF
        self.dequeue_bound_update(node)
        return node

    cpdef void filter_by_lb(self, double max_lb):
        """Keep only nodes whose lb < *max_lb*; call cleanup() on the rest.

        Delegates partitioning to the C++ ``filter()`` method: single linear
        pass + one ``make_heap`` on the surviving entries.  Only the removed
        entries are returned to Cython for ``node.cleanup()`` calls.
        """
        cdef:
            vector[PriNode] removed
            PriNode entry
            Node node
            size_t i

        removed = self.pq.filter(max_lb)   # O(n) partition + O(k log k) heap
        for i in range(removed.size()):
            entry = removed[i]             # transferred ownership
            node = <Node>entry.obj         # Cython INCREFs → refcount = 2
            _Py_DECREF(entry.obj)          # balance push INCREF → refcount = 1
            _Py_DECREF(entry.priority)     # release priority push INCREF
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
            PriNode entry
            Node node
            list nodes = []

        while not self.pq.empty():
            entry = self.pq.pop()
            node = <Node>entry.obj
            _Py_DECREF(entry.obj)
            _Py_DECREF(entry.priority)
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

    cpdef object make_priority(self, Node node):
        raise NotImplementedError("Subclasses must implement make_priority()")


# ---------------------------------------------------------------------------
# Concrete strategy subclasses
# ---------------------------------------------------------------------------

cdef class DfsCppPriQueue(CppPriorityQueue):
    """Depth-first ordering: ``(-level, lb, -index)``."""

    cpdef object make_priority(self, Node node):
        return (-node.level, node.lb, -node.get_index())


cdef class BfsCppPriQueue(CppPriorityQueue):
    """Breadth-first ordering: ``(level, lb, index)``."""

    cpdef object make_priority(self, Node node):
        return (node.level, node.lb, node.get_index())


cdef class BestCppPriQueue(CppPriorityQueue):
    """Best-first ordering: ``(lb, -level, -index)``."""

    cpdef object make_priority(self, Node node):
        return (node.lb, -node.level, -node.get_index())
