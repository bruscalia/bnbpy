# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.string cimport string

import logging
from typing import Literal, Optional

from bnbprob.slpfssp.cpp.environ cimport (
    JobPtr,
    Permutation,
    intensify_ref,
    local_search,
    neh_constructive
)
from bnbprob.slpfssp.cython.solution cimport FlowSolution
from bnbpy.cython.problem cimport Problem
from bnbpy.cython.solution cimport Solution
from bnbpy.cython.status cimport OptStatus

log = logging.getLogger(__name__)


cdef class PermFlowShop(Problem):

    def __init__(
        self,
        solution: FlowSolution
    ) -> None:
        self.solution = solution

    def __del__(self):
        self.ccleanup()

    cdef void ccleanup(PermFlowShop self):
        self.solution = None

    @classmethod
    def from_p(
        cls,
        p: list[list[list[int]]]
    ) -> 'PermFlowShop':
        cdef:
            Permutation perm
            FlowSolution solution
        perm = Permutation(p)
        solution = FlowSolution()
        solution.perm = perm
        return cls(
            solution
        )

    cpdef FlowSolution warmstart(PermFlowShop self):
        cdef:
            Permutation perm
            FlowSolution solution
            vector[JobPtr] jobs

        jobs = self.get_solution().perm.get_sequence_copy()
        perm = neh_constructive(jobs)
        solution = FlowSolution()
        solution.perm = perm
        return solution

    cpdef FlowSolution local_search(PermFlowShop self):
        cdef:
            double lb, new_cost
            Permutation perm
            FlowSolution sol_alt
            vector[JobPtr] jobs

        lb = self.solution.lb
        jobs = self.get_solution().perm.get_sequence_copy()
        perm = local_search(jobs)
        sol_alt = FlowSolution()
        sol_alt.perm = perm
        new_cost = perm.calc_lb_full()
        if new_cost < lb:
            sol_alt.set_lb(new_cost)
            sol_alt.set_feasible()
            return sol_alt
        return None

    cpdef FlowSolution intensification_ref(
        PermFlowShop self,
        FlowSolution ref_solution
    ):
        cdef:
            double new_cost, lb
            FlowSolution sol_alt, sol_ls
            vector[JobPtr] jobs

        sol_alt = FlowSolution()
        sol_alt.perm = intensify_ref(
            self.get_solution().perm,
            ref_solution.perm
        )
        new_cost = sol_alt.perm.calc_lb_full()
        sol_alt.set_lb(new_cost)
        sol_alt.set_feasible()

        return sol_alt

    cpdef double calc_bound(PermFlowShop self):
        return self.get_solution().perm.calc_lb_1m()

    cpdef bool is_feasible(PermFlowShop self):
        return self.get_solution().perm.is_feasible()

    cpdef list[PermFlowShop] branch(PermFlowShop self):
        # Get fixed and unfixed job lists to create new solution
        cdef:
            int j, J
            list[PermFlowShop] out

        J = self.get_solution().perm.free_jobs.size()
        out = [None] * J
        for j in range(J):
            out[j] = self._child_push(j)
        return out

    cdef PermFlowShop _child_push(PermFlowShop self, int& j):
        cdef:
            PermFlowShop child = self._copy()

        child.get_solution().push_job(j)
        return child

    cpdef void bound_upgrade(PermFlowShop self):
        cdef:
            double lb5, lb
            FlowSolution current

        current = self.get_solution()
        if current.perm.free_jobs.size() == 0:
            lb5 = <double>current.perm.calc_lb_full()
        else:
            lb5 = <double>current.lower_bound_2m()
        lb = max(self.solution.lb, lb5)
        self.solution.set_lb(lb)

    cpdef int calc_idle_time(PermFlowShop self):
        return self.get_solution().perm.calc_idle_time()

    cpdef PermFlowShop copy(PermFlowShop self, bool deep=False):
        return self._copy()

    cdef PermFlowShop _copy(PermFlowShop self):
        cdef:
            PermFlowShop child
        child = type(self).__new__(type(self))
        child.solution = self.solution._copy()
        return child


cdef class PermFlowShop2M(PermFlowShop):

    cpdef double calc_bound(PermFlowShop2M self):
        return self.get_solution().perm.calc_lb_2m()
