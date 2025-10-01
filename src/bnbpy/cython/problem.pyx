from libcpp cimport bool

import copy

from bnbpy.cython.solution cimport Solution
from bnbpy.cython.status cimport OptStatus


cdef class Problem:

    def __init__(self) -> None:
        self.solution = Solution()

    def __del__(self):
        self.cleanup()

    @property
    def lb(self):
        return self.get_lb()

    cpdef void cleanup(Problem self):
        self.solution = None

    cpdef double calc_bound(Problem self):
        raise NotImplementedError("Must implement `calc_bound` method")

    cpdef void compute_bound(Problem self):
        lb = self.calc_bound()
        self.solution.set_lb(lb)

    cpdef bool is_feasible(Problem self):
        raise NotImplementedError("Must implement `is_feasible` method")

    cpdef list[Problem] branch(Problem self):
        raise NotImplementedError("Must implement `branch` method")

    cpdef bool check_feasible(Problem self):
        cdef:
            bool feas
        feas = self.is_feasible()
        if feas:
            self.solution.set_feasible()
        else:
            self.solution.set_infeasible()
        return feas

    cpdef void set_solution(Problem self, Solution solution):
        self.solution = solution
        if self.solution.status == OptStatus.NO_SOLUTION:
            self.compute_bound()

    cpdef Problem warmstart(Problem self):
        return None

    cpdef Problem copy(self, bool deep=True):
        if deep:
            return self.deep_copy()
        return self.shallow_copy()
