# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool

import logging
from typing import List, Literal, Optional

from bnbprob.pfssp.cython.heuristics cimport (
    local_search as ls,
    neh_constructive as neh,
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
        self.cleanup()

    cpdef void cleanup(PermFlowShop self):
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
        """Instantiate problem based on processing times only

        Parameters
        ----------
        p : List[List[int]]
            Processing times for each job

        constructive: Literal['neh', 'quick']
            Constructive heuristic, by default 'neh'

        Returns
        -------
        PermFlowShop
            Instance of the problem
        """
        perm = Permutation.from_p(p)
        solution = FlowSolution(perm)
        return cls(
            solution,
            constructive=constructive,
        )

    def warmstart(self) -> FlowSolution:
        """
        Computes an initial feasible solution based on the method of choice.

        If the attribute `constructive` is 'neh', the heuristic
        of Nawaz et al. (1983) is adopted, otherwise
        the strategy by Palmer (1965).

        Returns
        -------
        FlowSolution
            Solution to the problem

        References
        ----------
        Nawaz, M., Enscore Jr, E. E., & Ham, I. (1983).
        A heuristic algorithm for the m-machine,
        n-job flow-shop sequencing problem.
        Omega, 11(1), 91-95.

        Palmer, D. S. (1965). Sequencing jobs through a multi-stage process
        in the minimum total time—a quick method of obtaining a near optimum.
        Journal of the Operational Research Society, 16(1), 101-107
        """
        if self.constructive == 'neh':
            return self.neh_constructive()
        return self.quick_constructive()

    def quick_constructive(self) -> FlowSolution:
        """Computes a feasible solution based on the sorting
        strategy by Palmer (1965).

        Returns
        -------
        FlowSolution
            Solution to the problem

        References
        ----------
        Palmer, D. S. (1965). Sequencing jobs through a multi-stage process
        in the minimum total time—a quick method of obtaining a near optimum.
        Journal of the Operational Research Society, 16(1), 101-107
        """
        perm = qc(self.solution.perm)
        return FlowSolution(perm)

    def neh_constructive(self) -> FlowSolution:
        """Constructive heuristic of Nawaz et al. (1983) based
        on best-insertion of jobs sorted according to total processing
        time in descending order.

        Returns
        -------
        FlowSolution
            Solution to the problem

        Reference
        ---------
        Nawaz, M., Enscore Jr, E. E., & Ham, I. (1983).
        A heuristic algorithm for the m-machine,
        n-job flow-shop sequencing problem.
        Omega, 11(1), 91-95.
        """
        perm = neh(self.solution.perm)
        return FlowSolution(perm)

    def local_search(self) -> Optional[FlowSolution]:
        """Local search heuristic from a current solution based on insertion

        Returns
        -------
        Optional[FlowSolution]
            New solution (best improvement) if exists
        """
        log.debug('Starting Heuristic')
        lb = self.solution.lb
        perm = ls(self.solution.perm)
        sol_alt = FlowSolution(perm)
        new_cost = sol_alt.perm.calc_bound()
        if new_cost < lb:
            return sol_alt
        return None

    cpdef int calc_bound(PermFlowShop self):
        return self.solution.perm.calc_bound()

    cpdef bool is_feasible(PermFlowShop self):
        return self.solution.perm.is_feasible()

    cpdef list[PermFlowShop] branch(PermFlowShop self):
        # Get fixed and unfixed job lists to create new solution
        return [
            self._child_push(j)
            for j in range(len(self.solution.free_jobs))
        ]

    cdef PermFlowShop _child_push(PermFlowShop self, int j):
        child = self.copy()
        child.solution.push_job(j)
        return child

    def bound_upgrade(self):
        lb5 = self.solution.perm.calc_lb_2m()
        lb = max(self.solution.lb, lb5)
        self.solution.set_lb(lb)

    cpdef PermFlowShop copy(PermFlowShop self):
        child_solution = self.solution.copy()
        child = type(self)(child_solution, self.constructive)
        return child


cdef class PermFlowShopLazy(PermFlowShop):

    cpdef int calc_bound(PermFlowShopLazy self):
        return self.solution.perm.calc_lb_1m()
