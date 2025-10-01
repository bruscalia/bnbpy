from typing import List, Literal, Optional

from bnbprob.pfssp.cython.pyjob import PyJob
from bnbpy.cython.counter import Counter

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

    constructive: str

    def __init__(
        self,
        constructive: Literal['neh', 'quick'] = 'neh',
    ) -> None: ...

    def __del__(self) -> None: ...

    def cleanup(self) -> None:
        """Clean up C++ resources."""
        ...

    @property
    def sequence(self) -> list[PyJob]:
        """Current job sequence."""
        ...

    @property
    def free_jobs(self) -> list[PyJob]:
        """List of unscheduled jobs."""
        ...

    @property
    def lb(self) -> float: ...

    def compute_bound(self) -> None: ...

    def check_feasible(self) -> bool: ...

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

    def quick_constructive(self) -> 'PermFlowShop':
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

    def neh_constructive(self) -> 'PermFlowShop':
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

    def ils(
        self,
        max_iter: int = 1000,
        max_age: int = 1000,
        d: int = 5,
        seed: int = 0
    ) -> 'PermFlowShop':
        """Iterated Local Search metaheuristic.

        Parameters
        ----------
        max_iter : int, optional
            Maximum number of iterations, by default 1000
        max_age : int, optional
            Maximum age for perturbation, by default 1000
        d : int, optional
            Perturbation strength, by default 5
        seed : int, optional
            Random seed, by default 0

        Returns
        -------
        PermFlowShop
            Improved solution
        """
        ...

    def randomized_heur(
        self,
        n_iter: int = 10,
        seed: int = 0
    ) -> 'PermFlowShop':
        """Randomized constructive heuristic.

        Parameters
        ----------
        n_iter : int, optional
            Number of iterations, by default 10
        seed : int, optional
            Random seed, by default 0

        Returns
        -------
        PermFlowShop
            Best solution found
        """
        ...

    def intensification(self) -> 'PermFlowShop':
        """Apply intensification procedure.

        Returns
        -------
        PermFlowShop
            Intensified solution
        """
        ...

    def intensification_ref(
        self, reference: 'PermFlowShop'
    ) -> 'PermFlowShop':
        """Apply intensification with reference solution.

        Parameters
        ----------
        reference : PermFlowShop
            Reference solution

        Returns
        -------
        PermFlowShop
            Intensified solution
        """
        ...

    def path_relinking(
        self, reference: 'PermFlowShop'
    ) -> 'PermFlowShop':
        """Apply path relinking with reference solution.

        Parameters
        ----------
        reference : PermFlowShop
            Reference solution

        Returns
        -------
        PermFlowShop
            Solution from path relinking
        """
        ...

    def calc_bound(self) -> float:
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

    def copy(self, deep: bool = False) -> 'PermFlowShop':
        """Create a copy of the problem.

        Parameters
        ----------
        deep : bool, optional
            Whether to perform deep copy, by default False

        Returns
        -------
        PermFlowShop
            Copy of the problem
        """
        ...

class PermFlowShop1M(PermFlowShop):
    """This approach uses the single machine bound upgrade
    in child problems.
    """

    def calc_bound(self) -> float:
        """Calculate single-machine lower bound only.

        Returns
        -------
        float
            Single-machine lower bound
        """
        ...

    def bound_upgrade(self) -> None:
        """No bound upgrade for single-machine approach."""
        ...

class PermFlowShop2MHalf(PermFlowShop):
    """This approach uses the two-machine bound upgrade
    in child problems, in nodes of which level is greater than
    or equal to floor(n/2) + 1, where n is the number of jobs.
    """

    def bound_upgrade(self) -> None:
        """Upgrade bound only after reaching half the jobs."""
        ...

class PermFlowShop2M(PermFlowShop):
    """This approach uses strictly the two-machine bound upgrade"""

    def calc_bound(self) -> float:
        """Calculate two-machine lower bound only.

        Returns
        -------
        float
            Two-machine lower bound
        """
        ...

class PermFlowShopLevelCount(PermFlowShop):
    """This approach counts bound upgrade performance by level."""

    lb_counter: object

    def bound_upgrade(self) -> None:
        """Upgrade bound and count performance by level."""
        ...

    def copy(self, deep: bool = False) -> 'PermFlowShopLevelCount':
        """Create a copy of the problem.

        Parameters
        ----------
        deep : bool, optional
            Whether to perform deep copy, by default False

        Returns
        -------
        PermFlowShopLevelCount
            Copy of the problem
        """
        ...

class PermFlowShopQuit(PermFlowShop):
    """This approach quits the two-machine bound upgrade
    in child problems if the single machine bound is better.
    The two-machine bound upgrade is resumed
    in nodes of which level is greater than
    or equal to floor(n/2) + 1, where n is the number of jobs.
    """

    def bound_upgrade(self) -> None:
        """Upgrade bound with adaptive strategy."""
        ...

    def copy(self, deep: bool = False) -> 'PermFlowShopQuit':
        """Create a copy of the problem.

        Parameters
        ----------
        deep : bool, optional
            Whether to perform deep copy, by default False

        Returns
        -------
        PermFlowShopQuit
            Copy of the problem
        """
        ...

class PermFlowShopCounter(PermFlowShopQuit):
    """This approach counts the number of times
    the two-machine bound upgrade is better than the single machine.
    """

    upgrade_counter: 'UpgradeCounter'

    def bound_upgrade(self) -> None:
        """Upgrade bound and count performance."""
        ...

    def copy(self, deep: bool = False) -> 'PermFlowShopCounter':
        """Create a copy of the problem.

        Parameters
        ----------
        deep : bool, optional
            Whether to perform deep copy, by default False

        Returns
        -------
        PermFlowShopCounter
            Copy of the problem
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

    def __init__(self) -> None:
        """Initialize all counters."""
        ...

    def to_dict(self) -> dict[str, int]:
        """Convert counters to dictionary.

        Returns
        -------
        dict[str, int]
            Dictionary with counter values
        """
        ...

def get_counts() -> tuple[int, int]:
    """Get global lb5 and lb1 counter values.

    Returns
    -------
    tuple[int, int]
        Tuple of (lb5_count, lb1_count)
    """
    ...
