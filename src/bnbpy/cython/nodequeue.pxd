# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

cimport cython
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
        NodePriEntry pop_min_bound()
        vector[NodePriEntry] filter(double max_lb)
        void clear()
        size_t size()
        bint empty()


@cython.final
cdef class NodePriQueueWrapper:

    cdef:
        NodePriQueue pq

    @cython.final
    cpdef void push(self, Node node, vector[double]& priority)

    @cython.final
    cpdef Node pop(self)

    @cython.final
    cpdef void filter(self, double max_lb)

    @cython.final
    cpdef size_t size(self)

    @cython.final
    cpdef void clear(self)
