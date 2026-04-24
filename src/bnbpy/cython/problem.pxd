from libcpp cimport bool

import copy

from bnbpy.cython.solution cimport Solution


ctypedef fused P:
    Problem


cdef class Problem:

    cdef public:
        Solution solution
        """Solution of the (sub)problem (if any)"""

    cpdef double calc_bound(self)

    cpdef bool is_feasible(self)

    cpdef list[Problem] branch(self)

    cdef inline double get_lb(self):
        return self.solution.lb

    cpdef void compute_bound(self)

    cpdef bool check_feasible(self)

    cpdef void set_solution(self, Solution solution)

    cpdef Problem warmstart(self)

    cpdef Problem primal_heuristic(self)

    cpdef double stronger_bound(self)

    cpdef void upgrade_bound(self, double new_lb)

    cpdef Problem copy(self, bool deep=*)

    cpdef Problem child_copy(self, bool deep=*)

    cdef inline Problem deep_copy(self):
        return copy.deepcopy(self)

    cdef inline Problem shallow_copy(self):
        return copy.copy(self)
