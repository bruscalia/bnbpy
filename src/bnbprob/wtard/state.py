from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class Job:
    index: int
    """
    Job unique identifier, also used as its bit in dominance bitmasks.
    """
    p: int
    """
    Processing time of the job.
    """
    w: int
    """
    Weight of the job.
    """
    d: int
    """
    Due date of the job.
    """
    dominated: int = 0
    """
    Bitmask of the jobs dominated by this job, i.e., jobs that can be
    assumed to be sequenced after it (Lemma 3.6.1 in Pinedo, 2008).
    """

    def dominates(self, other: 'Job') -> bool:
        """Checks whether this job dominates the other one: if
        ``p_j <= p_k``, ``d_j <= d_k`` and ``w_j >= w_k``, there is an
        optimal sequence in which job ``j`` appears before job ``k``.

        Identical jobs are ordered by index, so that the dominance
        relation never contains cycles.

        Parameters
        ----------
        other : Job
            Candidate job to be dominated.

        Returns
        -------
        bool
            Whether this job dominates the other one.
        """
        if self.p == other.p and self.d == other.d and self.w == other.w:
            return self.index < other.index
        return self.p <= other.p and self.d <= other.d and self.w >= other.w


@dataclass(slots=True)
class ProblemState:
    fixed: list[Job]
    """
    Jobs fixed at the end of the sequence, in reverse order,
    i.e., the last job of the sequence comes first.
    """
    remaining: list[Job]
    """
    Unscheduled jobs, sorted by nondecreasing due date
    (as expected by the relaxation).
    """
    remaining_mask: int
    """
    Bitmask of the unscheduled jobs. A job is eligible to be fixed next
    (backwards) only if it dominates none of them.
    """
    horizon: int
    """
    Total processing time of the unscheduled jobs, which is also the
    instant at which the fixed block starts.
    """
    fixed_cost: int
    """
    Total weighted tardiness of the fixed jobs.
    """

    def copy(self) -> 'ProblemState':
        """Returns a copy safe to modify by a child node.
        Jobs are immutable, so only the lists are copied."""
        return ProblemState(
            fixed=self.fixed.copy(),
            remaining=self.remaining.copy(),
            remaining_mask=self.remaining_mask,
            horizon=self.horizon,
            fixed_cost=self.fixed_cost,
        )
