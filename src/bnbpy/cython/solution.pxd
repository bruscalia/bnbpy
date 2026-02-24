# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool

from bnbpy.cython.status cimport OptStatus


cdef class Solution:

    cdef public:
        double cost
        """
        Upper bound of the solution
        (infinity in case of infeasibility or not being solved)
        """
        double lb
        """Lower bound of the solution"""
        OptStatus status
        """Optimization status of the solution"""

    cpdef void set_optimal(Solution self)

    cpdef void set_lb(Solution self, double lb)

    cpdef void set_feasible(Solution self)

    cpdef void set_infeasible(Solution self)

    cpdef void fathom(Solution self)

    cpdef Solution copy(Solution self, bool deep=*)

    cdef Solution _copy(Solution self)
