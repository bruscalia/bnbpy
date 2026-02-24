# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool

import copy

from bnbpy.cython.status cimport OptStatus


cdef extern from "math.h":
    double HUGE_VAL


cdef class Solution:
    """Solution representation"""

    def __init__(self):
        self.cost = HUGE_VAL
        self.lb = -HUGE_VAL
        self.status = OptStatus.NO_SOLUTION

    def __del__(self):
        pass

    def __repr__(self) -> str:
        return self._signature

    def __str__(self) -> str:
        return self._signature

    @property
    def _signature(self):
        cdef object status_ = self.status
        return (
            f'Status: {status_.name} | Cost: {self.cost} | LB: {self.lb}'
        )

    cpdef void set_optimal(Solution self):
        self.status = OptStatus.OPTIMAL

    cpdef void set_lb(Solution self, double lb):
        self.lb = lb
        if self.status == OptStatus.NO_SOLUTION:
            self.status = OptStatus.RELAXATION

    cpdef void set_feasible(Solution self):
        self.status = OptStatus.FEASIBLE
        self.cost = self.lb

    cpdef void set_infeasible(Solution self):
        self.status = OptStatus.INFEASIBLE
        self.cost = HUGE_VAL

    cpdef void fathom(Solution self):
        self.status = OptStatus.FATHOM
        self.cost = HUGE_VAL

    cpdef Solution copy(Solution self, bool deep=True):
        if deep:
            return copy.deepcopy(self)
        return self._copy()

    cdef Solution _copy(Solution self):
        cdef:
            Solution sol
        sol = Solution.__new__(Solution)
        sol.cost = self.cost
        sol.lb = self.lb
        sol.status = self.status
        return sol
