import logging
from typing import List, Literal, Optional

from bnbprob.pfssp.pypure.heuristics import (
    local_search as ls,
)
from bnbprob.pfssp.pypure.heuristics import (
    neh_constructive as neh,
)
from bnbprob.pfssp.pypure.heuristics import (
    quick_constructive as qc,
)
from bnbprob.pfssp.pypure.permutation import Permutation
from bnbprob.pfssp.pypure.solution import FlowSolution
from bnbpy import Problem

log = logging.getLogger(__name__)


class PermFlowShop(Problem):
    """Class to represent a permutation flow-shop scheduling problem
    with lower bounds computed by the max of a single machine and
    a two machine relaxations.

    The bounds for single and two-machine problems are described
    by Potts (1980), also implemented by Ladhari & Haouari (2005),
    therein described as 'LB1' and 'LB5'.

    If the attribute `constructive` is 'neh', the heuristic
    of Nawaz et al. (1983) is adopted, otherwise
    the strategy by Palmer (1965).

    References
    ----------
    Ladhari, T., & Haouari, M. (2005). A computational study of
    the permutation flow shop problem based on a tight lower bound.
    Computers & Operations Research, 32(7), 1831-1847.

    Nawaz, M., Enscore Jr, E. E., & Ham, I. (1983).
    A heuristic algorithm for the m-machine,
    n-job flow-shop sequencing problem.
    Omega, 11(1), 91-95.

    Potts, C. N. (1980). An adaptive branching rule for the permutation
    flow-shop problem. European Journal of Operational Research, 5(1), 19-25.

    Palmer, D. S. (1965). Sequencing jobs through a multi-stage process
    in the minimum total time—a quick method of obtaining a near optimum.
    Journal of the Operational Research Society, 16(1), 101-107
    """

    solution: FlowSolution
    m: int

    def __init__(
        self,
        solution: FlowSolution,
        constructive: Literal['neh', 'quick'] = 'neh',
    ) -> None:
        super().__init__()
        self.solution = solution
        self.constructive = constructive

    def __del__(self):
        self.cleanup()

    def cleanup(self) -> None:
        self.solution = None

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
        perm = qc(self.solution.perm.get_sequence_copy())
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
        perm = neh(self.solution.perm.get_sequence_copy())
        return FlowSolution(perm)

    def local_search(self) -> Optional[FlowSolution]:
        """Local search heuristic from a current solution based on insertion

        Returns
        -------
        Optional[FlowSolution]
            New solution (best improvement) if exists
        """
        lb = self.solution.lb
        perm = ls(self.solution.perm)
        sol_alt = FlowSolution(perm)
        new_cost = sol_alt.perm.calc_bound()
        if new_cost < lb:
            return sol_alt
        return None

    def calc_bound(self) -> int:
        return self.solution.perm.calc_lb_1m()

    def is_feasible(self) -> bool:
        return self.solution.perm.is_feasible()

    def branch(self) -> list['PermFlowShop']:
        # Get fixed and unfixed job lists to create new solution
        return [
            self._child_push(j)
            for j in range(len(self.solution.free_jobs))
        ]

    def _child_push(self, j: int) -> 'PermFlowShop':
        child = self.copy()
        child.solution.push_job(j)
        return child

    def bound_upgrade(self) -> None:
        if len(self.solution.perm.free_jobs) == 0:
            lb5 = self.solution.perm.calc_lb_full()
        else:
            lb5 = self.solution.perm.lower_bound_2m()
        lb = max(self.solution.lb, lb5)
        self.solution.set_lb(lb)

    def copy(self) -> 'PermFlowShop':
        child = type(self).__new__(type(self))
        child.solution = self.solution.copy()
        child.constructive = self.constructive
        return child


class PermFlowShop2M(PermFlowShop):

    def calc_bound(self) -> int:
        return self.solution.perm.calc_lb_2m()
