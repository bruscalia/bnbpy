# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from bnbpy.cython.node cimport Node
from bnbpy.cython.search cimport BranchAndBound

cdef:
    int RESTART = 10_000


cdef class LazyBnB(BranchAndBound):

    cpdef void post_eval_callback(LazyBnB self, Node node)


cdef class CallbackBnB(LazyBnB):

    cdef:
        int restart_freq
        int base_heur_factor
        int heur_factor
        int heur_calls
        int level_restart

    cpdef void solution_callback(CallbackBnB self, Node node)

    cpdef void intensify(CallbackBnB self, Node node)


cdef class CallbackBnBAge(CallbackBnB):

    cdef public:
        int sol_age

    cpdef Node dequeue(CallbackBnBAge self)
