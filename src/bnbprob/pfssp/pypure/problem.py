import logging
from typing import List, Literal, Optional

from bnbprob.pfssp.pypure.job import Job
from bnbprob.pfssp.pypure.solution import Permutation
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

    solution: Permutation
    m: int

    def __init__(
        self,
        m: int,
        jobs: Optional[List[Job]],
        constructive: Literal['neh', 'quick'] = 'neh',
    ) -> None:
        """Permutation Flow-Shop Problem

        Parameters
        ----------
        m : int
            Number of machines

        jobs : Optional[List[Job]]
            List of Jobs

        constructive: Literal['neh', 'quick']
            Constructive heuristic, by default 'neh'
        """
        super().__init__()
        self.m = m
        for j in jobs:
            j.fill_start(m)
        self.solution = Permutation(m, jobs)
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
        J = len(p)
        M = len(p[0])
        return cls(
            M,
            [
                Job(
                    j,
                    p[j],
                    [0 for _ in range(len(p[j]))],
                    [0 for _ in range(len(p[j]))],
                    [[]],
                )
                for j in range(J)
            ],
            constructive=constructive,
        )

    def warmstart(self) -> Permutation:
        """
        Computes an initial feasible solution based on the method of choice.

        If the attribute `constructive` is 'neh', the heuristic
        of Nawaz et al. (1983) is adopted, otherwise
        the strategy by Palmer (1965).

        Returns
        -------
        Permutation
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

    def quick_constructive(self) -> Permutation:
        """Computes a feasible solution based on the sorting
        strategy by Palmer (1965).

        Returns
        -------
        Permutation
            Solution to the problem

        References
        ----------
        Palmer, D. S. (1965). Sequencing jobs through a multi-stage process
        in the minimum total time—a quick method of obtaining a near optimum.
        Journal of the Operational Research Society, 16(1), 101-107
        """
        sol = Permutation(
            self.solution.m, [j.copy() for j in self.solution.free_jobs]
        )
        sol.free_jobs.sort(key=lambda x: x.slope, reverse=True)
        for _ in range(len(sol.free_jobs)):
            job = sol.free_jobs.pop(0)
            sol.sigma1.add_job(job)
        return sol

    def neh_constructive(self) -> Permutation:
        """Constructive heuristic of Nawaz et al. (1983) based
        on best-insertion of jobs sorted according to total processing
        time in descending order.

        Returns
        -------
        Permutation
            Solution to the problem

        Reference
        ---------
        Nawaz, M., Enscore Jr, E. E., & Ham, I. (1983).
        A heuristic algorithm for the m-machine,
        n-job flow-shop sequencing problem.
        Omega, 11(1), 91-95.
        """
        # Find best order of two jobs with longest processing times
        self.solution.free_jobs.sort(key=lambda x: sum(x.p), reverse=True)
        s1 = Permutation(self.solution.m, self.solution.free_jobs[:2])
        s2 = Permutation(
            self.solution.m,
            [self.solution.free_jobs[1], self.solution.free_jobs[0]],
        )
        c1 = s1.calc_bound()
        c2 = s2.calc_bound()
        if c1 <= c2:
            sol = s1
        else:
            sol = s2

        # Find best insert for every other job
        for j in self.solution.free_jobs[2:]:
            best_cost = float('inf')
            best_sol = None
            # Positions in sequence
            for i in range(len(sol.sequence) + 1):
                s_alt = Permutation(sol.m, sol.sequence)
                job = j.copy()
                s_alt.free_jobs.insert(i, job)
                # Fix all jobs
                for _ in range(len(s_alt.free_jobs)):
                    job_i = s_alt.free_jobs.pop(0)
                    s_alt.sigma1.add_job(job_i)
                cost_alt = s_alt.calc_bound()
                # Update best of iteration
                if cost_alt < best_cost:
                    best_cost = cost_alt
                    best_sol = s_alt
            sol = best_sol
        return sol

    def local_search(self) -> Optional[Permutation]:
        """Local search heuristic from a current solution based on insertion

        Returns
        -------
        Optional[Permutation]
            New solution (best improvement) if exists
        """
        log.debug('Starting Heuristic')

        # A new base solution following the same sequence of the current
        sol_base = Permutation(
            self.solution.m,
            [j.copy() for j in self.solution.sequence],
            level=self.solution.level,
        )

        # The release date in the first machine must be recomputed
        # As positions might change
        _recompute_r0(sol_base.free_jobs)
        best_move = None
        best_cost = self.solution.lb

        # Try to remove every job
        for i in range(len(sol_base.free_jobs)):
            # The current list decreases size in one unit after removal
            for j in range(len(sol_base.free_jobs)):
                # Job shouldn't be inserted in the same original position
                # and avoids symmetric swaps
                if j in {i, i + 1}:
                    continue

                # Here the swap is performed
                sol_alt = sol_base.copy()
                job = sol_alt.free_jobs.pop(i)
                sol_alt.free_jobs.insert(j, job)

                # In the new solution jobs are sequentially
                # inserted in the last position, so only sigma 1 is modified
                # Updates to sigma C for each machine are automatic
                for _ in range(len(sol_alt.free_jobs)):
                    job = sol_alt.free_jobs.pop(0)
                    sol_alt.sigma1.add_job(job)

                # New bound is computed considering sigma C
                new_cost = sol_alt.calc_bound()
                if new_cost < best_cost:
                    log.debug(f'Solution improvement! {new_cost}')
                    best_move = sol_alt
                    best_cost = new_cost

        return best_move

    def calc_bound(self) -> Optional[int]:
        return self.solution.calc_bound()

    def is_feasible(self):
        return self.solution.is_feasible()

    def branch(self) -> Optional[List['PermFlowShop']]:
        # Get fixed and unfixed job lists to create new solution
        children = [
            self._child_push(j) for j in range(len(self.solution.free_jobs))
        ]
        return children

    def _child_push(self, j: int):
        child = self.copy(deep=False)
        child.solution = self.solution.copy(deep=False)
        child.solution.push_job(j)
        return child

    def bound_upgrade(self):
        lb5 = self.solution.calc_lb_2m()
        lb = max(self.solution.lb, lb5)
        self.solution.set_lb(lb)


class PermFlowShopLazy(PermFlowShop):
    """
    Class to represent a permutation flow-shop scheduling problem
    with lower bounds computed by a single machine relaxation
    in the first evaluation and a combination of single machine
    and two-machine in the second.
    """

    def calc_bound(self) -> int | None:
        return self.solution.calc_lb_1m()


def _recompute_r0(jobs: List[Job]):
    jobs[0].r[0] = 0
    for j in range(1, len(jobs)):
        jobs[j].r[0] = jobs[j - 1].r[0] + jobs[j - 1].p[0]
