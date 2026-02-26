from libcpp cimport bool

import copy

from bnbpy.cython.solution cimport Solution


cdef class Problem:

    cdef public:
        Solution solution
        """Solution of the (sub)problem (if any)"""

    cpdef void cleanup(Problem self)

    cpdef double calc_bound(Problem self)

    cpdef bool is_feasible(Problem self)

    cpdef list[Problem] branch(Problem self)

    cdef inline double get_lb(Problem self):
        return self.solution.lb

    cpdef void compute_bound(Problem self)

    cpdef bool check_feasible(Problem self)

    cpdef void set_solution(Problem self, Solution solution)

    cpdef Problem warmstart(Problem self)

    cpdef Problem copy(self, bool deep=*)

    cpdef Problem child_copy(self, bool deep=*)

    cdef inline Problem deep_copy(Problem self):
        return copy.deepcopy(self)

    cdef inline Problem shallow_copy(Problem self):
        return copy.copy(self)
