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

    // POD entry stored in the C++ heap for NodePriQueue.
    // Lifetime: C++ heap owns one reference to obj.
    //   - push()              : Py_INCREF obj
    //   - pop() / pop_min_bound(): transfers ownership to caller (no DECREF)
    //   - clear() / filter()  : Py_DECREF obj for discarded entries
    struct NodePriEntry {
        PyObject* obj;
        double lb;
        std::vector<double> priority;
        NodePriEntry() : obj(nullptr), lb(0.0), priority() {}
        NodePriEntry(PyObject* o, double l, const std::vector<double>& p) : obj(o), lb(l), priority(p) {}
    };

    // Comparator: min-heap over vector<double> priorities.
    // C++ max-heap; a < b  <=>  a.priority > b.priority makes the smallest
    // priority bubble to the top.
    struct NodePriEntryLess {
        bool operator()(const NodePriEntry& a, const NodePriEntry& b) const {
            return a.priority > b.priority;
        }
    };

    struct NodePriQueue {
        std::vector<NodePriEntry> heap;
        NodePriEntryLess cmp;

        static constexpr size_t RESERVE_BLOCK = 100000;

        // Push: C++ takes ownership (INCREFs obj).
        // Capacity grows by RESERVE_BLOCK to amortise reallocations.
        void push(PyObject* obj, double lb, const std::vector<double>& priority) {
            if (heap.size() == heap.capacity()) {
                heap.reserve(heap.capacity() + RESERVE_BLOCK);
            }
            Py_INCREF(obj);
            heap.emplace_back(obj, lb, priority);
            std::push_heap(heap.begin(), heap.end(), cmp);
        }

        // Pop: transfers ownership to caller.
        // Shrinks capacity when it exceeds 2x new size by more than
        // RESERVE_BLOCK to prevent unbounded memory retention.
        NodePriEntry pop() {
            std::pop_heap(heap.begin(), heap.end(), cmp);
            NodePriEntry entry = heap.back();
            heap.pop_back();
            size_t sz = heap.size();
            if (heap.capacity() > 2 * sz + RESERVE_BLOCK) {
                heap.shrink_to_fit();
                heap.reserve(sz + RESERVE_BLOCK);
            }
            return entry;
        }

        // Returns a by-value copy with borrowed references (heap still owns).
        // Caller must NOT Py_DECREF the returned pointer.
        NodePriEntry min_bound_entry() const {
            size_t best = 0;
            for (size_t i = 1; i < heap.size(); ++i) {
                if (heap[i].lb < heap[best].lb) best = i;
            }
            return heap[best];
        }

        // pop_min_bound: transfers ownership to caller.
        // Same capacity-shrink policy as pop().
        NodePriEntry pop_min_bound() {
            size_t best = 0;
            for (size_t i = 1; i < heap.size(); ++i) {
                if (heap[i].lb < heap[best].lb) best = i;
            }
            NodePriEntry entry = heap[best];
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
            }
            heap.clear();
        }

        // Partition in-place: keep entries with lb < max_lb, return the rest.
        // Returned entries still carry their push INCREFs; caller must
        // Py_DECREF(entry.obj) for each removed entry.
        std::vector<NodePriEntry> filter(double max_lb) {
            std::vector<NodePriEntry> removed;
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
        double fill_min_lb_nodes(std::vector<NodePriEntry>& out) const {
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
    cdef cppclass NodePriEntry:
        PyObject* obj
        double lb
        vector[double] priority
        NodePriEntry()
        NodePriEntry(PyObject* o, double l, const vector[double]& p)

    cdef cppclass NodePriQueue:
        NodePriQueue()
        void push(PyObject* obj, double lb, const vector[double]& priority)
        NodePriEntry pop()
        NodePriEntry min_bound_entry()
        NodePriEntry pop_min_bound()
        vector[NodePriEntry] filter(double max_lb)
        double fill_min_lb_nodes(vector[NodePriEntry]& out)
        void clear()
        size_t size()
        bint empty()


cdef class PriorityManagerInterface(BaseNodeManager):
    """Priority queue manager backed by a native C++ binary heap.

    Stores nodes with ``vector[double]`` priorities; the queue is a
    *min*-heap (smallest priority dequeued first).

    Subclasses must override :meth:`make_priority`.
    """

    cdef:
        NodePriQueue pq
        double lb
        set[Node] bound_nodes

    cdef public:
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

    cpdef vector[double] make_priority(self, Node node)

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


cdef class BestFirstSearch(PriorityManagerInterface):
    """Best-first variant: priority ``(lb, -level, -index)``."""
    cpdef vector[double] make_priority(self, Node node)
