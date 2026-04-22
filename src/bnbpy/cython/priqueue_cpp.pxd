# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

from cpython.ref cimport PyObject
from libcpp cimport bool
from libcpp.vector cimport vector

from bnbpy.cython.manager cimport BaseNodeManager
from bnbpy.cython.node cimport Node


cdef extern from *:
    """
    #include <vector>
    #include <algorithm>

    // POD node entry stored in the C++ heap.
    // Lifetime: C++ heap owns one reference to both obj and priority.
    //   - push()            : Py_INCREF both
    //   - pop() / pop_min_bound(): transfers ownership to caller (no DECREF)
    //   - clear() / filter(): Py_DECREF both for discarded entries
    struct PriNode {
        PyObject* obj;
        double lb;
        PyObject* priority;
        PriNode() : obj(nullptr), lb(0.0), priority(nullptr) {}
    };

    // Comparator: implements min-heap over Python-comparable priorities.
    // C++ max-heap puts the "greatest" element on top.
    // Defining a < b  <=>  a.priority > b.priority (Python GT)
    // makes the element with the *smallest* Python priority bubble to the top.
    struct PyPriNodeLess {
        bool operator()(const PriNode& a, const PriNode& b) const {
            int r = PyObject_RichCompareBool(a.priority, b.priority, Py_GT);
            if (r < 0) { PyErr_Clear(); return false; }
            return r == 1;
        }
    };

    struct PyPriQueue {
        std::vector<PriNode> heap;
        PyPriNodeLess cmp;

        static constexpr size_t RESERVE_BLOCK = 100000;

        // Push: C++ takes ownership (INCREFs both obj and priority).
        // When the vector is full, grow capacity by RESERVE_BLOCK to avoid
        // repeated O(n) copy-reallocations on every doubling boundary.
        void push(PyObject* obj, double lb, PyObject* priority) {
            if (heap.size() == heap.capacity()) {
                heap.reserve(heap.capacity() + RESERVE_BLOCK);
            }
            PriNode e;
            e.obj = obj;
            e.lb = lb;
            e.priority = priority;
            Py_INCREF(obj);
            Py_INCREF(priority);
            heap.push_back(e);
            std::push_heap(heap.begin(), heap.end(), cmp);
        }

        // Pop: transfers ownership to caller.
        // Caller must Py_DECREF(entry.priority) and either use entry.obj
        // (Cython will INCREF it on cast) then Py_DECREF it to balance.
        // Shrinks capacity when it exceeds 2x the new size by more than
        // RESERVE_BLOCK, preventing unbounded memory retention after
        // large filter_by_lb calls.
        PriNode pop() {
            std::pop_heap(heap.begin(), heap.end(), cmp);
            PriNode entry = heap.back();
            heap.pop_back();
            size_t sz = heap.size();
            if (heap.capacity() > 2 * sz + RESERVE_BLOCK) {
                heap.shrink_to_fit();
                heap.reserve(sz + RESERVE_BLOCK);
            }
            return entry;
        }

        // Returns a by-value copy with *borrowed* references (heap still owns).
        // Caller must NOT Py_DECREF the returned pointers.
        PriNode min_bound_entry() const {
            size_t best = 0;
            for (size_t i = 1; i < heap.size(); ++i) {
                if (heap[i].lb < heap[best].lb) best = i;
            }
            return heap[best];
        }

        // pop_min_bound: transfers ownership to caller.
        // Same capacity-shrink policy as pop().
        PriNode pop_min_bound() {
            size_t best = 0;
            for (size_t i = 1; i < heap.size(); ++i) {
                if (heap[i].lb < heap[best].lb) best = i;
            }
            PriNode entry = heap[best];
            heap[best] = heap.back();
            heap.pop_back();
            if (!heap.empty()) {
                std::make_heap(heap.begin(), heap.end(), cmp);
            }
            size_t sz = heap.size();
            if (heap.capacity() > 2 * sz + RESERVE_BLOCK) {
                heap.shrink_to_fit();
                heap.reserve(sz + RESERVE_BLOCK);
            }
            return entry;
        }

        // Releases all owned references and empties the heap.
        void clear() {
            for (auto& e : heap) {
                Py_DECREF(e.obj);
                Py_DECREF(e.priority);
            }
            heap.clear();
        }

        // Partition heap in-place: keep entries with lb < max_lb, collect
        // the rest into the returned vector.  The returned entries still
        // carry their push INCREFs — the caller is responsible for
        // Py_DECREF(entry.obj) and Py_DECREF(entry.priority).
        // Kept entries retain their INCREFs untouched.
        std::vector<PriNode> filter(double max_lb) {
            std::vector<PriNode> removed;
            size_t keep = 0;
            for (size_t i = 0; i < heap.size(); ++i) {
                if (heap[i].lb < max_lb) {
                    heap[keep++] = heap[i];
                } else {
                    removed.push_back(heap[i]);
                }
            }
            heap.resize(keep);
            if (keep > 0) {
                std::make_heap(heap.begin(), heap.end(), cmp);
            }
            return removed;
        }

        // Fills `out` with borrowed entries tied at the minimum lb (two-pass).
        // All returned pointers are borrowed — caller must NOT Py_DECREF them.
        double fill_min_lb_nodes(std::vector<PriNode>& out) const {
            double min_lb = heap[0].lb;
            for (size_t i = 1; i < heap.size(); ++i)
                if (heap[i].lb < min_lb) min_lb = heap[i].lb;
            for (size_t i = 0; i < heap.size(); ++i)
                if (heap[i].lb == min_lb) out.push_back(heap[i]);
            return min_lb;
        }

        size_t size() const { return heap.size(); }
        bool empty() const { return heap.empty(); }
    };
    """
    cdef cppclass PriNode:
        PyObject* obj
        double lb
        PyObject* priority
        PriNode()

    cdef cppclass PyPriQueue:
        PyPriQueue()
        void push(PyObject* obj, double lb, PyObject* priority)
        PriNode pop()
        PriNode min_bound_entry()
        PriNode pop_min_bound()
        vector[PriNode] filter(double max_lb)
        double fill_min_lb_nodes(vector[PriNode]& out)
        void clear()
        size_t size()
        bint empty()


cdef class CppPriorityQueue(BaseNodeManager):
    """Priority queue backed by a native C++ binary heap.

    Priorities are arbitrary Python objects compared via Python's ``<``
    operator.  The queue behaves as a *min*-heap (smallest priority
    dequeued first), matching the semantics of :class:`PriorityQueue`.

    Subclasses must override :meth:`make_priority`.
    """

    cdef:
        PyPriQueue pq
        double lb
        set[Node] bound_nodes

    cdef public:
        # Profiling attributes (nanoseconds) — remove after benchmarking
        double enqueue_time
        double dequeue_time

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

    cpdef void reset_timers(self)

    cpdef object make_priority(self, Node node)

    cpdef double peek_lb(self)

    cpdef set[Node] get_bound_nodes(self)

    cdef inline void enqueue_bound_update(self, Node node):
        if node.lb <= self.lb:
            if node.lb < self.lb:
                self.lb = node.lb
                self.bound_nodes.clear()
            self.bound_nodes.add(node)

    cdef inline void dequeue_bound_update(self, Node node):
        if node.lb <= self.lb:
            self.bound_nodes.discard(node)


cdef class DfsCppPriQueue(CppPriorityQueue):
    """DFS variant: priority ``(-level, lb, -index)``."""
    cpdef object make_priority(self, Node node)


cdef class BfsCppPriQueue(CppPriorityQueue):
    """BFS variant: priority ``(level, lb, index)``."""
    cpdef object make_priority(self, Node node)


cdef class BestCppPriQueue(CppPriorityQueue):
    """Best-first variant: priority ``(lb, -level, -index)``."""
    cpdef object make_priority(self, Node node)
