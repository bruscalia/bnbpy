import logging
from typing import List, Literal, Optional

from bnbprob.pfssp.cython.solution import FlowSolution

log = logging.getLogger(__name__)

class PermFlowShop:
    """
    Class to represent a permutation flow-shop scheduling problem
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

    def __init__(
        self,
        solution: FlowSolution,
        constructive: Literal['neh', 'quick'] = 'neh',
    ) -> None:
        ...

    def __del__(self) -> None:
        ...

    def cleanup(self) -> None:
        ...

    @property
    def lb(self) -> float:
        ...

    def compute_bound(self) -> None:
        ...

    def check_feasible(self) -> bool:
        ...

    def set_solution(self, solution: FlowSolution) -> None:
        ...

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
        ...

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
        ...

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
        ...

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
        ...

    def local_search(self) -> Optional[FlowSolution]:
        """Local search heuristic from a current solution based on insertion

        Returns
        -------
        Optional[FlowSolution]
            New solution (best improvement) if exists
        """
        ...

    def calc_bound(self) -> int:
        ...

    def is_feasible(self) -> bool:
        ...

    def branch(self) -> list['PermFlowShop']:
        # Get fixed and unfixed job lists to create new solution
        ...

    def bound_upgrade(self) -> None:
        """
        Solves 2-machine subproblems to upgrade current lower bound
        """
        ...

    def copy(self) -> 'PermFlowShop':
        ...

class PermFlowShop2M(PermFlowShop):

    def calc_bound(self) -> int:
        ...
