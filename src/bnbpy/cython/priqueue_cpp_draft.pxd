# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from cpython.ref cimport PyObject
from libcpp cimport bool
from libcpp.vector cimport vector

from bnbpy.cython.node cimport Node


cdef extern from *:
    """
    #include <Python.h>
    #include <vector>
    #include <algorithm>

    struct PriBoundedNode {
        PyObject* obj;
        double lb;
        std::vector<double> priority;

        PriBoundedNode() : obj(nullptr), lb(0), priority() {}
        PriBoundedNode(PyObject* o, double l, const std::vector<double>& p) : obj(o), lb(l), priority(p) {}

        bool operator<(const PriBoundedNode& other) const {
            // Compare based on priority vector lexicographically
            return this->priority > other.priority;
        }
    };

    struct PriQueueBounded {
        std::vector<PriBoundedNode> heap;

        void push(PyObject* obj, double lb, const std::vector<double>& priority) {
            heap.push_back(PriBoundedNode(obj, lb, priority));
            std::push_heap(heap.begin(), heap.end());
        }

        PriBoundedNode pop() {
            std::pop_heap(heap.begin(), heap.end());
            PriBoundedNode entry = heap.back();
            heap.pop_back();
            return entry;
        }

        const PriBoundedNode& top() const {
            return heap.front();
        }

        void filter(double max_bound) {
            std::vector<PriBoundedNode> kept;
            kept.reserve(heap.size());
            for (auto& entry : heap) {
                if (entry.lb > max_bound) {
                    Py_XDECREF(entry.obj);
                } else {
                    kept.push_back(entry);
                }
            }
            heap = std::move(kept);
            std::make_heap(heap.begin(), heap.end());
        }

        // Find entry with smallest lb (linear scan).
        const PriBoundedNode& min_bound_entry() const {
            size_t best = 0;
            for (size_t i = 1; i < heap.size(); ++i) {
                if (heap[i].lb < heap[best].lb) {
                    best = i;
                }
            }
            return heap[best];
        }

        // Find and remove entry with smallest lb (linear scan + re-heapify).
        PriBoundedNode pop_min_bound() {
            size_t best = 0;
            for (size_t i = 1; i < heap.size(); ++i) {
                if (heap[i].lb < heap[best].lb) {
                    best = i;
                }
            }
            PriBoundedNode entry = heap[best];
            heap[best] = heap.back();
            heap.pop_back();
            if (!heap.empty()) {
                std::make_heap(heap.begin(), heap.end());
            }
            return entry;
        }

        size_t size() const {
            return heap.size();
        }

        bool empty() const {
            return heap.empty();
        }

        void clear() {
            for (auto& entry : heap) {
                Py_XDECREF(entry.obj);
            }
            heap.clear();
        }
    };
    """
    cppclass PriBoundedNode:
        PyObject* obj
        double lb
        vector[double] priority
        PriBoundedNode()
        PriBoundedNode(PyObject* o, double l, const vector[double]& p)

    cppclass PriQueueBounded:
        PriQueueBounded()
        void push(PyObject* obj, double lb, const vector[double]& priority)
        PriBoundedNode pop()
        void filter(double max_bound)
        const PriBoundedNode& min_bound_entry()
        PriBoundedNode pop_min_bound()
        const PriBoundedNode& top()
        size_t size()
        bint empty()
        void clear()


cdef class BasePriQueue:

    cpdef bint not_empty(BasePriQueue self)

    cpdef void enqueue(BasePriQueue self, Node node)

    cpdef Node dequeue(BasePriQueue self)

    cpdef Node get_lower_bound(BasePriQueue self)

    cpdef Node pop_lower_bound(BasePriQueue self)

    cpdef void clear(BasePriQueue self)

    cpdef void filter_by_lb(BasePriQueue self, double max_lb)


cdef class HeapPriQueue(BasePriQueue):

    cdef:
        PriQueueBounded pq

    cdef inline c_get_size(HeapPriQueue self):
        return self.pq.size()

    cpdef int get_size(HeapPriQueue self)

    cpdef bint not_empty(HeapPriQueue self)

    cpdef Node dequeue(HeapPriQueue self)

    cpdef Node get_lower_bound(HeapPriQueue self)

    cpdef Node pop_lower_bound(HeapPriQueue self)

    cpdef void filter_by_lb(HeapPriQueue self, double max_lb)

    cpdef void clear(HeapPriQueue self)


cdef class DFSPriQueue(HeapPriQueue):

    cpdef void enqueue(DFSPriQueue self, Node node)


cdef class BFSPriQueue(HeapPriQueue):

    cpdef void enqueue(BFSPriQueue self, Node node)


cdef class BestPriQueue(HeapPriQueue):

    cpdef void enqueue(BestPriQueue self, Node node)

