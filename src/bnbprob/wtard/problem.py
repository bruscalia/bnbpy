from dataclasses import replace
from math import exp, inf
from typing import Sequence

from bnbpy import Problem

from .lagrangian import LagrangianBound
from .relaxation import preemptive_bound
from .state import Job, ProblemState

ATC_SCALES = (0.5, 1.0, 2.0, 3.0, 4.0, 5.0)
"""Values of the look-ahead parameter K tried by the ATC warmstart."""


class WeightedTardiness(Problem):
    """Total weighted tardiness problem 1 || sum w_j T_j.

    Sequences are built backwards (Pinedo, 2008, Section 3.6): each
    branch fixes one of the unscheduled jobs in the last free position.
    Branching skips jobs that dominate an unscheduled job (Lemma 3.6.1)
    and nodes whose unscheduled jobs were already reached by a fixed
    sequence of no higher cost. The lower bound is the tardiness of the
    fixed jobs plus the best between the transportation relaxation and
    the Lagrangian relaxation of the unscheduled ones.
    """

    state: ProblemState
    """
    Current state of the weighted tardiness problem.
    """
    _tail_costs: dict[int, int]
    """
    Lowest cost of the fixed jobs found for each set of unscheduled jobs
    (bitmask), shared among nodes. Nodes with the same unscheduled jobs
    share the same subproblem, so only the cheapest one is explored.
    """
    _lagrangian: LagrangianBound
    """
    Lagrangian bound with multipliers adjusted to the ATC sequence of the
    root node, shared among nodes.
    """

    def __init__(self, state: ProblemState) -> None:
        super().__init__()
        self.state = state
        self._tail_costs = {}
        self._lagrangian = LagrangianBound.from_sequence(
            self._best_atc_sequence()
        )

    @classmethod
    def from_data(
        cls, p: Sequence[int], w: Sequence[int], d: Sequence[int]
    ) -> 'WeightedTardiness':
        """Creates the root problem from processing times, weights
        and due dates, computing dominance relations among jobs.

        Parameters
        ----------
        p : Sequence[int]
            Processing times.

        w : Sequence[int]
            Weights.

        d : Sequence[int]
            Due dates.

        Returns
        -------
        WeightedTardiness
            Root problem with no fixed jobs.
        """
        if not len(p) == len(w) == len(d):
            raise ValueError('p, w and d must have the same length')
        if min([*p, *w, *d], default=0) < 0:
            raise ValueError('p, w and d must be non-negative')
        jobs = [Job(index=j, p=p[j], w=w[j], d=d[j]) for j in range(len(p))]
        jobs = [
            replace(job, dominated=cls._dominance_mask(job, jobs))
            for job in jobs
        ]
        state = ProblemState(
            fixed=[],
            remaining=sorted(jobs, key=lambda job: (job.d, job.index)),
            remaining_mask=(1 << len(jobs)) - 1,
            horizon=sum(p),
            fixed_cost=0,
        )
        return cls(state)

    @property
    def sequence(self) -> list[Job]:
        """Unscheduled jobs (by due date) followed by the fixed ones."""
        return self.state.remaining + self.state.fixed[::-1]

    def calc_bound(self) -> int:
        state = self.state
        return state.fixed_cost + max(
            preemptive_bound(state.remaining, state.horizon),
            self._lagrangian.evaluate(state.remaining_mask),
        )

    def is_feasible(self) -> bool:
        return not self.state.remaining

    def branch(self) -> list['WeightedTardiness']:
        state = self.state
        # Same unscheduled jobs reached later at a lower cost
        if state.fixed_cost > self._tail_costs.get(state.remaining_mask, inf):
            return []
        children = []
        for i, job in enumerate(state.remaining):
            # A job dominating an unscheduled one must precede it
            if job.dominated & state.remaining_mask:
                continue
            mask = state.remaining_mask & ~(1 << job.index)
            cost = state.fixed_cost + job.w * max(state.horizon - job.d, 0)
            # Same unscheduled jobs already reached at no higher cost
            if cost >= self._tail_costs.get(mask, inf):
                continue
            self._tail_costs[mask] = cost
            child = self.child_copy(deep=False)
            child._fix_job(i)
            children.append(child)
        return children

    def clean_cache(self) -> None:
        """Clears the costs of fixed sequences shared among nodes,
        required to search again from the same problem instance."""
        self._tail_costs.clear()

    def warmstart(self) -> 'WeightedTardiness':
        """Completes the sequence of unscheduled jobs by the Apparent
        Tardiness Cost (ATC) rule (Pinedo, 2008, Chapter 14), keeping the
        best sequence among the values of K in ``ATC_SCALES``.

        Returns
        -------
        WeightedTardiness
            Copy of the problem with all jobs fixed
        """
        sol = self.child_copy(deep=False)
        # Jobs are fixed backwards, so the last job comes first
        for job in reversed(self._best_atc_sequence()):
            sol._fix_job(sol.state.remaining.index(job))
        return sol

    def _best_atc_sequence(self) -> list[Job]:
        if not self.state.remaining:
            return []
        return min(
            (self._atc_sequence(k) for k in ATC_SCALES),
            key=self._sequence_cost,
        )

    def _atc_sequence(self, k: float) -> list[Job]:
        """Sequences the unscheduled jobs from time zero, each time picking
        the job with the largest index
        ``w_j / p_j * exp(-max(d_j - p_j - t, 0) / (k * p_mean))``."""
        remaining = self.state.remaining.copy()
        scale = k * (self.state.horizon / len(remaining) or 1)
        sequence = []
        t = 0
        while remaining:
            # Ties keep the due date order of remaining jobs
            job = max(
                remaining, key=lambda job: self._atc_index(job, t, scale)
            )
            remaining.remove(job)
            sequence.append(job)
            t += job.p
        return sequence

    @staticmethod
    def _atc_index(job: Job, t: int, scale: float) -> float:
        if not job.p:
            return inf
        return job.w / job.p * exp(-max(job.d - job.p - t, 0) / scale)

    @staticmethod
    def _sequence_cost(sequence: Sequence[Job]) -> int:
        t = 0
        cost = 0
        for job in sequence:
            t += job.p
            cost += job.w * max(t - job.d, 0)
        return cost

    def child_copy(self, deep: bool = False) -> 'WeightedTardiness':
        other = super().child_copy(deep)
        other.state = self.state.copy()
        return other

    def _fix_job(self, i: int) -> None:
        """Fixes the i-th unscheduled job in the last free position."""
        state = self.state
        job = state.remaining.pop(i)
        state.fixed.append(job)
        state.remaining_mask &= ~(1 << job.index)
        state.fixed_cost += job.w * max(state.horizon - job.d, 0)
        state.horizon -= job.p

    @staticmethod
    def _dominance_mask(job: Job, jobs: Sequence[Job]) -> int:
        mask = 0
        for other in jobs:
            if other is not job and job.dominates(other):
                mask |= 1 << other.index
        return mask


class TransportOnly(WeightedTardiness):
    def calc_bound(self) -> int:
        return self.state.fixed_cost + preemptive_bound(
            self.state.remaining, self.state.horizon
        )
