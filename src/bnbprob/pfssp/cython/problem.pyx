# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool

import logging
from typing import List, Literal, Optional

from bnbprob.pfssp.cython.heuristics cimport (
    local_search as ls,
)
from bnbprob.pfssp.cython.heuristics cimport (
    neh_constructive as neh,
)
from bnbprob.pfssp.cython.heuristics cimport (
    quick_constructive as qc,
)
from bnbprob.pfssp.cython.permutation cimport Permutation
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
        perm = Permutation.from_p(p)
        solution = FlowSolution(perm)
        return cls(
            solution,
            constructive=constructive,
        )

    cpdef FlowSolution warmstart(PermFlowShop self):
        if self.constructive == 'neh':
            return self.neh_constructive()
        return self.quick_constructive()

    cpdef FlowSolution quick_constructive(PermFlowShop self):
        perm = qc(self.solution.perm.get_sequence_copy())
        return FlowSolution(perm)

    cpdef FlowSolution neh_constructive(PermFlowShop self):
        perm = neh(self.solution.perm.get_sequence_copy())
        return FlowSolution(perm)

    cpdef FlowSolution local_search(PermFlowShop self):
        cdef:
            int lb, new_cost
            Permutation perm
            FlowSolution sol_alt
        lb = self.solution.lb
        perm = ls(self.solution.perm)
        sol_alt = FlowSolution(perm)
        new_cost = sol_alt.perm.calc_lb_full()
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

    cdef PermFlowShop _child_push(PermFlowShop self, int j):
        cdef:
            PermFlowShop child = self.copy()
        child.solution.push_job(j)
        return child

    cpdef void bound_upgrade(PermFlowShop self):
        cdef:
            int lb5, lb

        if <int>len(self.solution.perm.free_jobs) == 0:
            lb5 = self.solution.perm.calc_lb_full()
        else:
            lb5 = self.solution.perm.lower_bound_2m()
        lb = max(self.solution.lb, lb5)
        self.solution.set_lb(lb)

    cpdef PermFlowShop copy(PermFlowShop self):
        cdef:
            PermFlowShop child
        child = type(self).__new__(type(self))
        child.solution = self.solution.copy()
        child.constructive = self.constructive
        return child


cdef class PermFlowShop2M(PermFlowShop):

    cpdef int calc_bound(PermFlowShop2M self):
        return self.solution.perm.calc_lb_2m()
