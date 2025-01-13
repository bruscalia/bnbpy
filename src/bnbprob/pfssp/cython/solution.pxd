# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool

from bnbprob.pfssp.cython.permutation cimport Permutation


cdef:
    int LARGE_INT = 10000000


cdef class FlowSolution:

    cdef public:
        int cost, lb
        Permutation perm
        object status

    cpdef void set_optimal(FlowSolution self)

    cpdef void set_lb(FlowSolution self, int lb)

    cpdef void set_feasible(FlowSolution self)

    cpdef void set_infeasible(FlowSolution self)

    cpdef void fathom(FlowSolution self)

    cpdef bool is_feasible(FlowSolution self)

    cpdef int calc_lb_1m(FlowSolution self)

    cpdef int calc_lb_2m(FlowSolution self)

    cpdef int lower_bound_1m(FlowSolution self)

    cpdef int lower_bound_2m(FlowSolution self)

    cpdef void push_job(FlowSolution self, int j)

    cpdef FlowSolution copy(FlowSolution self)