import heapq
import logging
from collections import defaultdict
from typing import Collection

from bnbprob.machdeadline.job import Job
from bnbpy import Problem

log = logging.getLogger(__name__)


LARGE_INT = 100000000


class MachDeadlineProb(Problem):
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
    _unscheduled_term: int
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
    _is_dominated: bool
    """Whether the current node is dominated by another one.
    Useful for dominance rules.
    """
    _lb_refs: dict[int, int]
    """References to lower bounds for dominance rules, indexed by the mask."""

    def __init__(self, jobs: Collection[Job]) -> None:
        super().__init__()
        self._fixed = []
        self._unscheduled = list(jobs)
        self._precumputed = False
        self._fixed_term = 0
        self._unscheduled_term = 0
        self._unscheduled_total_time = sum(job.p for job in self._unscheduled)
        self._violations = False
        self._mask = 0
        self._is_dominated = False
        self._lb_refs = defaultdict(lambda: LARGE_INT)
        MachDeadlineProb.find_wspt(self._unscheduled)
        self._compute_completion_times()

    @property
    def sequence(self) -> list[Job]:
        return self._unscheduled + list(reversed(self._fixed))

    def write(self) -> str:
        return '->'.join([f'{job}' for job in self.sequence])

    def _compute_completion_times(self) -> None:
        last_c = 0
        self._violations = False
        self._unscheduled_term = 0
        for job in self._unscheduled:
            c = last_c + job.p
            last_c = c
            self._unscheduled_term += job.w * c
            if c > job.d:
                self._violations = True
        self._precumputed = True

    def calc_bound(self) -> int:
        if not self._precumputed:
            self._compute_completion_times()
        cost = self._unscheduled_term + self._fixed_term
        # This will cause the early pruning
        # of dominated nodes
        if cost >= self._lb_refs[self._mask]:
            self._is_dominated = True
            return cost
        self._lb_refs[self._mask] = cost
        return cost

    def is_feasible(self) -> bool:
        if not self._precumputed:
            self._compute_completion_times()
        return not self._violations

    def branch(self) -> list['MachDeadlineProb']:
        # Early pruning of dominated nodes
        if self._is_dominated:
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
        self._precumputed = False

    def warmstart(self) -> 'MachDeadlineProb | None':
        sol = self.child_copy(deep=False)
        smith_jobs = sol.smith_rule()
        if not smith_jobs:
            return None
        for job in smith_jobs:
            sol.fix_job(job)
        return sol

    def smith_rule(self) -> list[Job]:
        tot_time = self._unscheduled_total_time
        pool = sorted(self._unscheduled, key=lambda j: j.d, reverse=False)
        sol: list[Job] = []
        candidates: list[tuple[float, Job]] = []
        for _ in range(len(self._unscheduled)):
            MachDeadlineProb._update_pool(pool, candidates, tot_time)
            if len(candidates) == 0:
                return []
            next_job = heapq.heappop(candidates)[1]
            sol.append(next_job)
            tot_time -= next_job.p

        return sol

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

    def child_copy(self, deep: bool = True) -> 'MachDeadlineProb':
        other = super().child_copy(deep)
        # In case of a shallow copy,
        # we need to make sure to copy the mutable attributes.
        # Notice jobs are immutable, so we can just pass on the references.
        other._fixed = self._fixed.copy()
        other._unscheduled = self._unscheduled.copy()
        other._precumputed = self._precumputed
        other._fixed_term = self._fixed_term
        other._unscheduled_term = self._unscheduled_term
        other._unscheduled_total_time = self._unscheduled_total_time
        other._violations = self._violations
        # Mask is immutable, so we can just pass on the reference
        other._mask = self._mask
        other._is_dominated = False
        # Shared reference
        other._lb_refs = self._lb_refs
        return other

    @staticmethod
    def find_wspt(jobs: list[Job]) -> None:
        jobs.sort(key=lambda job: job.w / job.p, reverse=True)


# Noted to implement the Lagrangian lower-bound to Smith's rule,
# as described in Potts & Van Wassenhove (1983):

# 1) Use Smith's rule to sort unscheduled jobs (ok).
# 2) Partition job blocks, revise the rule (not clear)
# 3) Compute lagrangian multipliers
# 4) Use multipliers for a tighter lower bound
