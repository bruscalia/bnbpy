# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool

from bnbprob.pfssp.cpp.environ cimport Permutation
from bnbpy.cython.solution cimport Solution


cdef class FlowSolution(Solution):

    cdef:
        Permutation perm

    cpdef bool is_feasible(FlowSolution self)

    cpdef int calc_lb_1m(FlowSolution self)

    cpdef int calc_lb_2m(FlowSolution self)

    cpdef int lower_bound_1m(FlowSolution self)

    cpdef int lower_bound_2m(FlowSolution self)

    cpdef void push_job(FlowSolution self, int& j)

    cdef void _push_job(FlowSolution self, int& j)

    cpdef void compute_starts(FlowSolution self)

    cpdef FlowSolution copy(FlowSolution self, bool deep=*)

    cdef FlowSolution _copy(FlowSolution self)
