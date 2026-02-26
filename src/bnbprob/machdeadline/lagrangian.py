import heapq
import logging
import sys
from collections import defaultdict
from dataclasses import dataclass
from math import ceil
from typing import Collection

from bnbprob.machdeadline.job import Job
from bnbprob.machdeadline.smith import SmithHelper
from bnbpy import Problem

log = logging.getLogger(__name__)


LARGE_INT = 100000000


@dataclass(slots=True)
class UnscheduledCosts:
    real: int
    lagrangian: int


class LagrangianDeadline(Problem):
    _fixed: list[Job]
    """End sequence in reverse order,
    i.e. the last scheduled job is the first in the list"""
    _unscheduled: list[Job]
    """Unsceduled jobs, sorted by WSPT rule in correct order"""
    _precumputed: bool
    """Indicates whether the completion times
    have been precalculated for the unscheduled jobs."""
    _fixed_term: int
    """Term of the objective function for the fixed part of the sequence"""
    _unscheduled_term: UnscheduledCosts
    """Term of the objective function for the unscheduled
    part of the sequence"""
    _violations: bool
    """Whether the current sequence has any deadline delay violation"""
    _unscheduled_total_time: int
    """Total processing time of the unscheduled jobs"""
    _mask: int
    """Mask for hashing and equality, based on the sequence of schedules jobs.
    Useful for dominance rules.
    """
    _lagrangian: 'LagrangianHelper'
    """Helper for computing the lagrangian multipliers and blocks."""
    _is_dominated: bool
    """Whether the current node is dominated by another one.
    Useful for dominance rules.
    """
    _lb_refs: dict[int, int]
    """References to lower bounds for dominance rules, indexed by the mask."""

    def __init__(self, jobs: Collection[Job]) -> None:
        super().__init__()
        self._fixed = []
        # Compute the total time before sorting,
        # as it is needed for the lagrangian helper
        self._unscheduled_total_time = sum(job.p for job in jobs)
        self._lagrangian = LagrangianHelper(
            list(jobs), total_time=self._unscheduled_total_time
        )
        self._unscheduled = self._lagrangian.smith
        self._precumputed = False
        self._fixed_term = 0
        self._unscheduled_term = UnscheduledCosts(0, 0)
        self._mask = 0
        self._is_dominated = False
        self._lb_refs = defaultdict(lambda: LARGE_INT)
        self._compute_completion_times()

    @property
    def sequence(self) -> list[Job]:
        return self._unscheduled + list(reversed(self._fixed))

    def write(self) -> str:
        return '->'.join([f'{job}' for job in self.sequence])

    def _compute_completion_times(self) -> None:
        real_term = 0
        lag_term = 0.0
        lags = self._lagrangian.lagrangian_multipliers
        C = self._lagrangian.completion_times
        for i, job in enumerate(self._unscheduled):
            real_term += job.w * C[i]
            lag_term += (job.w + lags[i]) * C[i] - lags[i] * job.d

        self._unscheduled_term = UnscheduledCosts(
            real=real_term, lagrangian=ceil(lag_term)
        )
        self._precumputed = True

    def calc_bound(self) -> int:
        if not self._precumputed:
            self._compute_completion_times()
        if not self._lagrangian.success:
            # If the lagrangian helper failed to find a solution,
            # by the Smith's rule,
            # it means that the current node is strictly infeasible
            return sys.maxsize
        cost = self._unscheduled_term.lagrangian + self._fixed_term
        # This will cause the early pruning
        # of dominated nodes
        if self._fixed_term >= self._lb_refs[self._mask]:
            self._is_dominated = True
            return cost
        self._lb_refs[self._mask] = self._fixed_term
        return cost

    def calc_real_cost(self) -> int:
        if not self._precumputed:
            self._compute_completion_times()
        return self._unscheduled_term.real + self._fixed_term

    def is_feasible(self) -> bool:
        return len(self._unscheduled) == 0

    def branch(self) -> list['LagrangianDeadline']:
        # Early pruning of dominated nodes
        if self._is_dominated or not self._lagrangian.success:
            return []
        # Create one child for each possible job to schedule next
        children = []
        for job in self._unscheduled:
            # Early infeasibility check
            if job.d < self._unscheduled_total_time:
                continue
            child = self.child_copy(deep=False)
            child.fix_job(job)
            children.append(child)
        return children

    def fix_job(self, job: Job) -> None:
        self._fixed.append(job)
        self._unscheduled.remove(job)
        self._mask |= 1 << job.id
        self._fixed_term += job.w * self._unscheduled_total_time
        self._unscheduled_total_time -= job.p
        self._lagrangian = LagrangianHelper(
            self._unscheduled, total_time=self._unscheduled_total_time
        )
        self._unscheduled = self._lagrangian.smith
        self._precumputed = False

    def warmstart(self) -> 'LagrangianDeadline | None':
        if not self._lagrangian.success:
            return None
        sol = self.child_copy(deep=False)
        sol._fix_all_self()
        return sol

    def _fix_all_self(self) -> None:
        for job in reversed(self._unscheduled):
            self._simple_fix_job(job)
        self._unscheduled.clear()
        self._unscheduled_term = UnscheduledCosts(0, 0)
        self._precumputed = True

    def _simple_fix_job(self, job: Job) -> None:
        self._fixed.append(job)
        self._mask |= 1 << job.id
        self._fixed_term += job.w * self._unscheduled_total_time
        self._unscheduled_total_time -= job.p

    @staticmethod
    def _update_pool(
        pool: list[Job], candidates: list[tuple[float, Job]], tot_time: int
    ) -> None:
        for _ in range(len(pool)):
            if pool[-1].d >= tot_time:
                job = pool.pop()
                heapq.heappush(candidates, (job.w / job.p, job))
            else:
                break

    def child_copy(self, deep: bool = True) -> 'LagrangianDeadline':
        other = super().child_copy(deep)
        # In case of a shallow copy,
        # we need to make sure to copy the mutable attributes.
        # Notice jobs are immutable, so we can just pass on the references.
        other._fixed = self._fixed.copy()
        other._unscheduled = self._unscheduled.copy()
        # Mask is immutable, so we can just pass on the reference
        other._mask = self._mask
        other._is_dominated = False
        other._lb_refs = self._lb_refs
        return other


class LagrangianHelper:
    smith: list[Job]
    completion_times: list[int]
    lagrangian_multipliers: list[float]
    blocks: list[list[Job]]
    success: bool

    def __init__(self, jobs: list[Job], total_time: int | None = None) -> None:
        self.completion_times = []
        self.lagrangian_multipliers = []
        self.blocks = []
        self._compute(jobs, total_time)

    def _compute(self, jobs: list[Job], total_time: int | None = None) -> None:
        smith_results = SmithHelper.apply(
            jobs, total_time=total_time, reverse=True
        )
        self.smith = smith_results.jobs
        self.success = smith_results.success
        self._calc_completion_times()
        self.blocks = self._get_blocks()
        self.lagrangian_multipliers = self._calc_lagrangian_multipliers()

    def _calc_completion_times(self) -> None:
        c = 0
        for job in self.smith:
            c += job.p
            self.completion_times.append(c)

    def _get_blocks(self) -> list[list[Job]]:
        if len(self.smith) == 0:
            return []
        blocks: list[list[Job]] = []
        job = self.smith[0]
        current_block = [job]
        blocks = [current_block]
        max_d = job.d
        for i, job in enumerate(self.smith[1:-1], start=1):
            # If the next job's deadline
            # is less than the current completion time
            max_d = max(max_d, job.d)
            if max_d > self.completion_times[i + 1]:
                current_block.append(job)
            else:
                current_block = [job]
                blocks.append(current_block)
        current_block.append(self.smith[-1])
        return blocks

    def _calc_lagrangian_multipliers(self) -> list[float]:
        rev_lagrange: list[float] = []
        for block in reversed(self.blocks):
            if len(block) == 0:
                continue
            lag_mult = 0.0
            rev_lagrange.append(lag_mult)
            last_job = block[-1]
            for job in reversed(block[:-1]):
                lag_mult = max(
                    0.0, (job.p / last_job.p) * (last_job.w + lag_mult) - job.w
                )
                rev_lagrange.append(lag_mult)
                last_job = job
        rev_lagrange.reverse()
        return rev_lagrange
