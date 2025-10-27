# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool

from bnbpy.cython.node cimport Node
from bnbpy.cython.search cimport BranchAndBound

cdef:
    int RESTART = 10_000


cdef class LazyBnB(BranchAndBound):

    cdef public:
        bool delay_lb5
        int min_lb5_level

    cpdef void post_eval_callback(LazyBnB self, Node node)


cdef class CallbackBnB(LazyBnB):

    cdef:
        int base_heur_factor
        int heur_factor
        int heur_calls

    cpdef void solution_callback(CallbackBnB self, Node node)

    cpdef void intensify(CallbackBnB self, Node node)
