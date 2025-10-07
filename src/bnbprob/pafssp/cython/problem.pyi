import logging
from typing import List, Literal, Optional, Tuple

from bnbprob.pafssp.cython.pyjob import PyJob
from bnbprob.pafssp.cython.pysigma import PySigma
from bnbprob.pafssp.machinegraph import MachineGraph
from bnbpy.cython.counter import Counter

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

    def __init__(
        self,
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

    @property
    def sequence(self) -> List[PyJob]:
        """Get the current job sequence"""
        ...

    @property
    def free_jobs(self) -> List[PyJob]:
        """Get the list of free (unscheduled) jobs"""
        ...

    @property
    def sigma1(self) -> PySigma:
        """Get the current sigma1 (partial permutation of jobs)"""
        ...

    @property
    def sigma2(self) -> PySigma:
        """Get the current sigma2 (partial permutation of jobs)"""
        ...

    def get_mach_graph(self) -> MachineGraph:
        """Get the machine graph for the problem"""
        ...

    def get_sigma1_mach_graph(self) -> MachineGraph:
        """Get the sigma1 machine graph"""
        ...

    def get_sigma2_mach_graph(self) -> MachineGraph:
        """Get the sigma2 machine graph"""
        ...

    def compute_bound(self) -> None:
        ...

    def check_feasible(self) -> bool:
        ...

    @classmethod
    def from_p(
        cls,
        p: List[List[int]],
        edges: Optional[List[Tuple[int, int]]] = None,
        constructive: Literal['neh', 'quick'] = 'neh'
    ) -> 'PermFlowShop':
        """Instantiate problem based on processing times and machine graph

        Parameters
        ----------
        p : List[List[int]]
            Processing times for each job

        edges : Optional[List[Tuple[int, int]]], optional
            Machine graph edges, by default None (sequential)

        constructive: Literal['neh', 'quick']
            Constructive heuristic, by default 'neh'

        Returns
        -------
        PermFlowShop
            Instance of the problem
        """
        ...

    def warmstart(self) -> 'PermFlowShop':
        """
        Computes an initial feasible solution based on the method of choice.

        If the attribute `constructive` is 'neh', the heuristic
        of Nawaz et al. (1983) is adopted, otherwise
        the strategy by Palmer (1965).

        Returns
        -------
        PermFlowShop
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

    def quick_constructive(self) -> PermFlowShop:
        """Computes a feasible solution based on the sorting
        strategy by Palmer (1965).

        Returns
        -------
        PermFlowShop
            Solution to the problem

        References
        ----------
        Palmer, D. S. (1965). Sequencing jobs through a multi-stage process
        in the minimum total time—a quick method of obtaining a near optimum.
        Journal of the Operational Research Society, 16(1), 101-107
        """
        ...

    def neh_constructive(self) -> PermFlowShop:
        """Constructive heuristic of Nawaz et al. (1983) based
        on best-insertion of jobs sorted according to total processing
        time in descending order.

        Returns
        -------
        PermFlowShop
            Solution to the problem

        Reference
        ---------
        Nawaz, M., Enscore Jr, E. E., & Ham, I. (1983).
        A heuristic algorithm for the m-machine,
        n-job flow-shop sequencing problem.
        Omega, 11(1), 91-95.
        """
        ...

    def local_search(self) -> Optional['PermFlowShop']:
        """Local search heuristic from a current solution based on insertion

        Returns
        -------
        Optional[PermFlowShop]
            New solution (best improvement) if exists
        """
        ...

    def randomized_heur(self, n_iter: int, seed: int = 0) -> 'PermFlowShop':
        """Multistart randomized heuristic: shuffle jobs, neh_core,
        local search

        Parameters
        ----------
        n_iter : int
            Number of iterations for the randomized heuristic
        seed : int, optional
            Random seed for reproducibility. If 0 (default), uses random device

        Returns
        -------
        PermFlowShop
            Best solution found across all iterations
        """
        ...

    def intensification(self) -> 'PermFlowShop':
        """Apply intensification to improve current solution

        Returns
        -------
        PermFlowShop
            Improved solution
        """
        ...

    def intensification_ref(self, reference: 'PermFlowShop') -> 'PermFlowShop':
        """Apply intensification with reference solution

        Parameters
        ----------
        reference : PermFlowShop
            Reference solution for intensification

        Returns
        -------
        PermFlowShop
            Improved solution
        """
        ...

    def calc_bound(self) -> float:
        """Calculate lower bound for the current state"""
        ...

    def is_feasible(self) -> bool:
        """Check if current state represents a feasible solution"""
        ...

    def branch(self) -> List['PermFlowShop']:
        """Generate child problems by branching"""
        ...

    def bound_upgrade(self) -> None:
        """Upgrade current lower bound using advanced techniques"""
        ...

    def calc_lb_1m(self) -> int:
        """Calculate single-machine lower bound"""
        ...

    def calc_lb_2m(self) -> int:
        """Calculate two-machine lower bound"""
        ...

    def lower_bound_1m(self) -> int:
        """Get single-machine lower bound"""
        ...

    def lower_bound_2m(self) -> int:
        """Get two-machine lower bound"""
        ...

    def push_job(self, j: int) -> None:
        """Push job to the sequence"""
        ...

    def compute_starts(self) -> None:
        """Compute start times for all jobs"""
        ...

    def calc_idle_time(self) -> int:
        """Calculate total idle time"""
        ...

    def calc_tot_time(self) -> int:
        """Calculate total completion time"""
        ...

    def copy(self, deep: bool = False) -> 'PermFlowShop':
        """Create a copy of the problem instance"""
        ...

class PermFlowShop1M(PermFlowShop):
    """This approach uses the single machine bound upgrade
    in child problems.
    """

    def calc_bound(self) -> float:
        """Calculate single-machine lower bound"""
        ...

    def bound_upgrade(self) -> None:
        """Override to disable bound upgrade"""
        ...

class PermFlowShop2MHalf(PermFlowShop):
    """This approach uses the two-machine bound upgrade
    in child problems, in nodes of which level is greater than
    or equal to floor(n/2) + 1, where n is the number of jobs.
    """

    def bound_upgrade(self) -> None:
        """Conditionally apply two-machine bound upgrade"""
        ...

class PermFlowShop2M(PermFlowShop):
    """This approach uses strictly the two-machine bound upgrade"""

    def calc_bound(self) -> float:
        """Calculate two-machine lower bound"""
        ...

class PermFlowShopQuit(PermFlowShop):
    """This approach quits the two-machine bound upgrade
    in child problems if the single machine bound is better.
    The two-machine bound upgrade is resumed
    in nodes of which level is greater than
    or equal to floor(n/2) + 1, where n is the number of jobs.
    """
    ...

class PermFlowShopCounter(PermFlowShopQuit):
    """This approach counts the number of times
    the two-machine bound upgrade is better than the single machine.
    """
    ...

class UpgradeCounter:
    """Counter for the number of times the two-machine bound upgrade
    is better than the single machine bound.
    """
    stay_two_mach: Counter
    switch_to_single: Counter
    stay_single: Counter
    switch_to_two_mach: Counter
