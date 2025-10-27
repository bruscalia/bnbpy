import logging
from typing import List, Literal, Optional, Tuple

from bnbprob.pafssp.cython.pyjob import PyJob
from bnbprob.pafssp.cython.pysigma import PySigma
from bnbprob.pafssp.machinegraph import MachineGraph
from bnbpy.cython.problem import Problem

log = logging.getLogger(__name__)

Constructive = Literal['neh', 'quick', 'multistart', 'iga']

class PermFlowShop(Problem):
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
        constructive: Constructive = 'neh',
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
        constructive: Constructive = 'neh'
    ) -> 'PermFlowShop':
        """Instantiate problem based on processing times and machine graph

        Parameters
        ----------
        p : List[List[int]]
            Processing times for each job

        edges : Optional[List[Tuple[int, int]]], optional
            Machine graph edges, by default None (sequential)

        constructive: Constructive
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

    def neh_initialization(self) -> PermFlowShop:
        """Constructive heuristic of Nawaz et al. (1983) based
        on best-insertion of jobs sorted according to total processing
        time in descending order.

        The complete heuristic has a time complexity of O(m n^2).

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

    def multistart_initialization(self) -> PermFlowShop:
        """Multistart constructive heuristic based on
        multiple iterations of random shuffling of jobs,
        NEH-like insertion based constructive, and local search.

        The complete heuristic has a time complexity of O(k m n^2),
        where k is the number of iterations (default number of jobs
        times number of machines). The random seed is fixed as 42.

        Returns
        -------
        PermFlowShop
            Solution to the problem
        """
        ...

    def iga_initialization(self) -> PermFlowShop:
        """Iterated Greedy Algorithm (IGA) heuristic
        by Ruiz and Stützle (2007).

        1) NEH greedy initialization;
        2) local search;
        3) perturbation by d random removals.

        The complete heuristic has a time complexity of O(k m n^2),
        where k is the number of iterations (default number of jobs
        times number of machines). The random seed is fixed as 42.

        Returns
        -------
        PermFlowShop
            Solution to the problem

        Reference
        ---------
        Ruiz, R., & Stützle, T. (2007). A simple and effective iterated
        greedy algorithm for the permutation flowshop scheduling problem.
        European Journal of Operational Research, 177(3), 2033-2049.
        """
        ...

    def local_search(self) -> Optional['PermFlowShop']:
        """Local search heuristic from a current solution based on insertion.
        Each iteration considers all possible insertions of each job
        in the current sequence, and performs the best improving move.
        Each iteration has a time complexity of O(m n^2).

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

    def iga_heur(self, n_iter: int, d: int, seed: int = 0) -> 'PermFlowShop':
        """Iterated Greedy Algorithm (IGA) heuristic
        by Ruiz and Stützle (2007).

        1) NEH greedy initialization;
        2) local search;
        3) perturbation by d random removals.

        Parameters
        ----------
        n_iter : int
            Number of iterations for the IGA heuristic

        d : int
            Number of random removed jobs for perturbation

        seed : int, optional
            Random seed for reproducibility. If 0 (default), uses random device

        Returns
        -------
        PermFlowShop
            Best solution found across all iterations

        Reference
        ---------
        Ruiz, R., & Stützle, T. (2007). A simple and effective iterated
        greedy algorithm for the permutation flowshop scheduling problem.
        European Journal of Operational Research, 177(3), 2033-2049.
        """
        ...

    def intensify(self, reference: 'PermFlowShop') -> 'PermFlowShop':
        """Apply intensification with reference solution.

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
        """Calculate lower bound for the current state.
        At the initial moment, solely a single machine bound is computed.
        The bound can be upgraded via `simple_bound_upgrade` and/or
        `double_bound_upgrade`.

        See `calc_lb_1m` and `calc_lb_2m` for details."""
        ...

    def is_feasible(self) -> bool:
        """Check if current state represents a feasible solution
        (all jobs scheduled)."""
        ...

    def branch(self) -> List['PermFlowShop']:
        """Generate child problems by branching."""
        ...

    def simple_bound_upgrade(self) -> None:
        """Upgrade current lower bound using tighter release dates
        and wait times with time complexity of O(m n)."""
        ...

    def double_bound_upgrade(self) -> None:
        """Upgrade current lower bound using two-machine relaxations
        with time complexity of O(m^2 n).

        By default, this method is called only in nodes of which
        level is greater than or equal to floor(n/3) + 1."""
        ...

    def calc_lb_1m(self) -> int:
        """Calculate single-machine lower bound."""
        ...

    def calc_lb_2m(self) -> int:
        """Calculate two-machine lower bound."""
        ...

    def lower_bound_1m(self) -> int:
        """Get raw single-machine lower bound with time complexity of O(m)."""
        ...

    def lower_bound_2m(self) -> int:
        """Get raw two-machine lower bound with time complexity of O(m^2 n)."""
        ...

    def update_params(self) -> None:
        """Updates parameters `r` and `q` of instance based on partial
        scheduling sigma1 and sigma2 and free jobs
        with time complexity of O(m n)."""
        ...

    def push_job(self, j: int) -> None:
        """Push job to the sequence."""
        ...

    def compute_starts(self) -> None:
        """Compute start times for all jobs."""
        ...

    def calc_idle_time(self) -> int:
        """Calculate total idle time with time complexity of O(m)."""
        ...

    def calc_tot_time(self) -> int:
        """Calculate total completion time with time complexity of O(m)."""
        ...

    def copy(self, deep: bool = False) -> 'PermFlowShop':
        """Create a copy of the problem instance"""
        ...

class BenchPermFlowShop(PermFlowShop):

    def calc_bound(self) -> float:
        """Calls `update_params` and computes a single machine bound.

        Returns
        -------
        float
            Single machine lower bound
        """
        ...

class PermFlowShop1M(PermFlowShop):
    """This approach uses the single machine bound upgrade
    in child problems.
    """

    def calc_bound(self) -> float:
        """Calculate single-machine lower bound."""
        ...

    def double_bound_upgrade(self) -> None:
        """Override to disable bound upgrade."""
        ...
