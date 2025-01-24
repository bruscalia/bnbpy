from libcpp cimport bool

import copy

from bnbpy.cython.solution cimport Solution


cdef class Problem:

    cdef public:
        Solution solution

    cpdef void cleanup(Problem self)

    cpdef double calc_bound(Problem self)

    cpdef bool is_feasible(Problem self)

    cpdef list[Problem] branch(Problem self)

    cdef inline double get_lb(Problem self):
        return self.solution.lb

    cpdef void compute_bound(Problem self)

    cdef inline bool check_feasible(Problem self):
        cdef:
            bool feas
        feas = self.is_feasible()
        if feas:
            self.solution.set_feasible()
        else:
            self.solution.set_infeasible()
        return feas

    cpdef void set_solution(Problem self, Solution solution)

    cpdef Solution warmstart(Problem self)

    cpdef copy(self, bool deep=*)

    cdef inline Problem deep_copy(Problem self):
        return copy.deepcopy(self)

    cdef inline Problem shallow_copy(Problem self):
        return copy.copy(self)
