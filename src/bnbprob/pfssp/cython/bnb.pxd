# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from bnbpy.cython.node cimport Node
from bnbpy.cython.search cimport BranchAndBound

cdef:
    int RESTART = 10_000


cdef class LazyBnB(BranchAndBound):

    cpdef void post_eval_callback(LazyBnB self, Node node)


cdef class CallbackBnB(LazyBnB):

    cdef public:
        int restart_freq

    cpdef void solution_callback(CallbackBnB self, Node node)


cdef Node _min_queue(list[tuple[object, Node]] queue)



cdef class CallbackBnBAge(CallbackBnB):

    cdef public:
        int sol_age

    cpdef Node dequeue(CallbackBnBAge self)
