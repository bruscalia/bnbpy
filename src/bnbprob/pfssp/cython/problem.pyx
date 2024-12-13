# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True

from bnbprob.pfssp.cython.solution cimport CyPermutation

import logging
from typing import List, Literal, Optional

from bnbpy import Problem

log = logging.getLogger(__name__)


class PermFlowShop(Problem):
    """Class to represent a permutation flow-shop scheduling problem
    with lower bounds computed by the max of a single machine and
    a two machine relaxations.

    The bounds for single and two-machine problems are described
    by Potts (1980), also implemented by Ladhari & Haouari (2005),
    therein described as 'LB1' and 'LB5'.

    The warmstart strategy is proposed by Palmer (1965).

    References
    ----------
    Ladhari, T., & Haouari, M. (2005). A computational study of
    the permutation flow shop problem based on a tight lower bound.
    Computers & Operations Research, 32(7), 1831-1847.

    Potts, C. N. (1980). An adaptive branching rule for the permutation
    flow-shop problem. European Journal of Operational Research, 5(1), 19-25.

    Palmer, D. S. (1965). Sequencing jobs through a multi-stage process
    in the minimum total time—a quick method of obtaining a near optimum.
    Journal of the Operational Research Society, 16(1), 101-107
    """

    solution: CyPermutation

    def __init__(
        self,
        solution: CyPermutation,
        constructive: Literal['neh', 'quick'] = 'neh',
    ) -> None:
        """Permutation Flow-Shop Problem

        Parameters
        ----------
        solution : CyPermutation
            Permutation solution

        constructive: Literal['neh', 'quick']
            Constructive heuristic, by default 'neh'
        """
        super().__init__()
        self.solution = solution
        self.constructive = constructive

    @classmethod
    def from_p(
        cls, p: List[List[int]], constructive: Literal['neh', 'quick'] = 'neh'
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
        permutation = CyPermutation.from_p(p)
        return cls(
            permutation,
            constructive=constructive,
        )

    def warmstart(self) -> CyPermutation:
        """
        Computes an initial feasible solution based on the method of choice.

        If the attribute `constructive` is 'neh', the heuristic
        of Nawaz et al. (1983) is adopted, otherwise
        the strategy by Palmer (1965).

        Returns
        -------
        CyPermutation
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
            return self.solution.neh_constructive()
        return self.solution.quick_constructive()

    def quick_constructive(self) -> CyPermutation:
        """Computes a feasible solution based on the sorting
        strategy by Palmer (1965).

        Returns
        -------
        CyPermutation
            Solution to the problem

        References
        ----------
        Palmer, D. S. (1965). Sequencing jobs through a multi-stage process
        in the minimum total time—a quick method of obtaining a near optimum.
        Journal of the Operational Research Society, 16(1), 101-107
        """
        return self.solution.quick_constructive()

    def neh_constructive(self) -> CyPermutation:
        """Constructive heuristic of Nawaz et al. (1983) based
        on best-insertion of jobs sorted according to total processing
        time in descending order.

        Returns
        -------
        CyPermutation
            Solution to the problem

        Reference
        ---------
        Nawaz, M., Enscore Jr, E. E., & Ham, I. (1983).
        A heuristic algorithm for the m-machine,
        n-job flow-shop sequencing problem.
        Omega, 11(1), 91-95.
        """
        return self.solution.neh_constructive()

    def local_search(self) -> Optional[CyPermutation]:
        """Local search heuristic from a current solution based on insertion

        Returns
        -------
        Optional[CyPermutation]
            New solution (best improvement) if exists
        """
        log.debug('Starting Heuristic')

        # A new base solution following the same sequence of the current
        return self.solution.local_search()

    def calc_bound(self) -> Optional[int]:
        return self.solution.calc_bound()

    def is_feasible(self):
        return self.solution.is_feasible()

    def branch(self) -> Optional[List['PermFlowShop']]:
        # Get fixed and unfixed job lists to create new solution
        cdef:
            int J
        J = self.solution.n_free
        children = [
            self._child_push(j) for j in range(J)
        ]
        return children

    def _child_push(self, j: int):
        child = self.copy()
        child.solution.push_job(j)
        return child

    def bound_upgrade(self):
        lb5 = self.solution.calc_lb_2m()
        lb = max(self.solution.lb, lb5)
        self.solution.set_lb(lb)

    def copy(self):
        return PermFlowShop(self.solution.copy(), self.constructive)


class PermFlowShopLazy(PermFlowShop):
    """
    Class to represent a permutation flow-shop scheduling problem
    with lower bounds computed by a single machine relaxation
    in the first evaluation and a combination of single machine
    and two-machine in the second.
    """

    def calc_bound(self) -> int | None:
        return self.solution.calc_lb_1m()

    def _child_push(self, j: int):
        child = self.copy()
        child.solution.push_job(j)
        return child

    def copy(self):
        return PermFlowShopLazy(self.solution.copy(), self.constructive)
