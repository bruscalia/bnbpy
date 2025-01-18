# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector

import logging
from typing import List, Literal, Optional

from bnbprob.pfssp.cpp.job cimport JobPtr
from bnbprob.pfssp.cpp.permutation cimport Permutation
from bnbprob.pfssp.cpp.local_search cimport local_search
from bnbprob.pfssp.cpp.neh cimport neh_constructive
from bnbprob.pfssp.cpp.quick_constructive cimport quick_constructive
from bnbprob.pfssp.cython.solution cimport FlowSolution
from bnbpy.status import OptStatus

log = logging.getLogger(__name__)


cdef class PermFlowShop:

    def __init__(
        self,
        solution: FlowSolution,
        constructive: Literal['neh', 'quick'] = 'neh',
    ) -> None:
        self.solution = solution
        self.constructive = constructive

    def __del__(self):
        self.ccleanup()

    cpdef void cleanup(PermFlowShop self):
        self.solution = None

    cdef void ccleanup(PermFlowShop self):
        self.solution = None

    @property
    def lb(self):
        return self.solution.lb

    cpdef void compute_bound(PermFlowShop self):
        lb = self.calc_bound()
        self.solution.set_lb(lb)

    cpdef bool check_feasible(PermFlowShop self):
        feas = self.is_feasible()
        if feas:
            self.solution.set_feasible()
        else:
            self.solution.set_infeasible()
        return feas

    cpdef void set_solution(PermFlowShop self, object solution):
        self.solution = solution
        if self.solution.status == OptStatus.NO_SOLUTION:
            self.compute_bound()

    @classmethod
    def from_p(
        cls,
        p: List[List[int]],
        constructive: Literal['neh', 'quick'] = 'neh'
    ) -> 'PermFlowShop':
        cdef:
            Permutation perm
            FlowSolution solution
        perm = Permutation(p)
        solution = FlowSolution()
        solution.perm = perm
        return cls(
            solution,
            constructive=constructive,
        )

    cpdef FlowSolution warmstart(PermFlowShop self):
        if self.constructive == 'neh':
            return self.neh_constructive()
        return self.quick_constructive()

    cpdef FlowSolution quick_constructive(PermFlowShop self):
        cdef:
            Permutation perm
            FlowSolution solution
            vector[JobPtr] jobs

        jobs = self.solution.perm.get_sequence_copy()
        perm = quick_constructive(jobs)
        solution = FlowSolution()
        solution.perm = perm
        return solution

    cpdef FlowSolution neh_constructive(PermFlowShop self):
        cdef:
            Permutation perm
            FlowSolution solution
            vector[JobPtr] jobs

        jobs = self.solution.perm.get_sequence_copy()
        perm = neh_constructive(jobs)
        solution = FlowSolution()
        solution.perm = perm
        return solution

    cpdef FlowSolution local_search(PermFlowShop self):
        cdef:
            int lb, new_cost
            Permutation perm
            FlowSolution sol_alt
        lb = self.solution.lb
        perm = local_search(self.solution.perm)
        sol_alt = FlowSolution()
        sol_alt.perm = perm
        new_cost = perm.calc_lb_full()
        if new_cost < lb:
            return sol_alt
        return None

    cpdef int calc_bound(PermFlowShop self):
        return self.solution.perm.calc_lb_1m()

    cpdef bool is_feasible(PermFlowShop self):
        return self.solution.perm.is_feasible()

    cpdef list[PermFlowShop] branch(PermFlowShop self):
        # Get fixed and unfixed job lists to create new solution
        cdef:
            int j
        return [
            self._child_push(j)
            for j in range(len(self.solution.free_jobs))
        ]

    cdef PermFlowShop _child_push(PermFlowShop self, int& j):
        cdef:
            PermFlowShop child = self._copy()
        child.solution.push_job(j)
        return child

    cpdef void bound_upgrade(PermFlowShop self):
        cdef:
            int lb5, lb

        if <int>self.solution.perm.free_jobs.size() == 0:
            lb5 = self.solution.perm.calc_lb_full()
        else:
            lb5 = self.solution.perm.lower_bound_2m()
        lb = max(self.solution.lb, lb5)
        self.solution.set_lb(lb)

    cpdef PermFlowShop copy(PermFlowShop self):
        return self._copy()

    cdef PermFlowShop _copy(PermFlowShop self):
        cdef:
            PermFlowShop child
        child = type(self).__new__(type(self))
        child.solution = self.solution._copy()
        child.constructive = self.constructive
        return child


cdef class PermFlowShop2M(PermFlowShop):

    cpdef int calc_bound(PermFlowShop2M self):
        return self.solution.perm.calc_lb_2m()
