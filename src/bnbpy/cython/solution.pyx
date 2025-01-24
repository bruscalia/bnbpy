# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool

import copy

from bnbpy.cython.status cimport OptStatus


cdef extern from "math.h":
    double HUGE_VAL


STATUS_MAP = {
    0: 'NO_SOLUTION',
    1: 'RELAXATION',
    2: 'OPTIMAL',
    3: 'FEASIBLE',
    4: 'INFEASIBLE',
    5: 'FATHOM',
    6: 'ERROR',
    7: 'OTHER',
}


cdef class Solution:

    def __init__(self):
        self.cost = HUGE_VAL
        self.lb = -HUGE_VAL
        self._status = OptStatus.NO_SOLUTION

    def __del__(self):
        pass

    def __repr__(self) -> str:
        return self._signature

    def __str__(self) -> str:
        return self._signature

    @property
    def status(self):
        return STATUS_MAP[<int>self._status]

    @property
    def _signature(self):
        return (
            f'Status: {self.status} | Cost: {self.cost} | LB: {self.lb}'
        )

    cpdef void set_optimal(Solution self):
        self._status = OptStatus.OPTIMAL

    cpdef void set_lb(Solution self, double lb):
        self.lb = lb
        if self._status == OptStatus.NO_SOLUTION:
            self._status = OptStatus.RELAXATION

    cpdef void set_feasible(Solution self):
        self._status = OptStatus.FEASIBLE
        self.cost = self.lb

    cpdef void set_infeasible(Solution self):
        self._status = OptStatus.INFEASIBLE
        self.cost = HUGE_VAL

    cpdef void fathom(Solution self):
        self._status = OptStatus.FATHOM
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
        sol._status = OptStatus.NO_SOLUTION
        return sol
