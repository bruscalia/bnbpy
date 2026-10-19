"""
Lagrangian lower bound for 1 || sum w_j T_j (Potts and Van Wassenhove,
1985).

Relaxing the constraints T_j >= C_j - d_j with multipliers
0 <= mu_j <= w_j leaves the problem

    L(mu) = min  sum_j mu_j C_j - sum_j mu_j d_j

solved exactly by the WSPT rule with weights mu_j. The multipliers are
adjusted to maximize L(mu) among those for which a given (heuristic)
sequence is WSPT optimal, i.e., mu_j / p_j is nonincreasing along it. In
that case L(mu) = sum_j mu_j L_j, in which L_j is the lateness of job j in
the sequence.

Writing the ratios as rho_k = mu_k / p_k = sum_{i >= k} delta_i, with
delta_i >= 0, the objective becomes sum_i delta_i S_i, in which S_i is the
prefix sum of p_k L_k, subject to the nested constraints
sum_{i >= k} delta_i <= w_k / p_k. Constraints over a chain of sets define
a polymatroid, so increasing each delta_i as much as possible by
nonincreasing S_i is optimal.
"""

from dataclasses import dataclass
from math import ceil
from typing import Sequence

from .state import Job

TOL = 1e-9
"""Tolerance for rounding up fractional bounds."""


@dataclass(slots=True, frozen=True)
class LagrangianBound:
    sequence: tuple[Job, ...]
    """
    Jobs with positive processing times, in an optimal order for the
    Lagrangian problem.
    """
    multipliers: tuple[float, ...]
    """
    Multiplier of each job in ``sequence``.
    """

    @classmethod
    def from_sequence(cls, sequence: Sequence[Job]) -> 'LagrangianBound':
        """Adjusts the multipliers to a sequence of jobs processed
        from time zero.

        Parameters
        ----------
        sequence : Sequence[Job]
            Heuristic sequence of jobs.

        Returns
        -------
        LagrangianBound
            Bound with the best multipliers for the sequence.
        """
        # Jobs without processing time get null multipliers
        jobs = [job for job in sequence if job.p]
        t = 0
        prefix = 0.0
        prefixes = []
        for job in jobs:
            t += job.p
            prefix += job.p * (t - job.d)
            prefixes.append(prefix)

        slack = [job.w / job.p for job in jobs]
        deltas = [0.0] * len(jobs)
        for i in sorted(range(len(jobs)), key=lambda i: -prefixes[i]):
            if prefixes[i] <= 0:
                break
            step = min(slack[: i + 1])
            if step <= 0:
                continue
            deltas[i] = step
            for k in range(i + 1):
                slack[k] -= step

        ratio = 0.0
        multipliers = [0.0] * len(jobs)
        for k in reversed(range(len(jobs))):
            ratio += deltas[k]
            multipliers[k] = min(ratio * jobs[k].p, jobs[k].w)
        return cls(sequence=tuple(jobs), multipliers=tuple(multipliers))

    def evaluate(self, mask: int) -> int:
        """Lagrangian bound of a subset of jobs processed from time zero,
        keeping the multipliers fixed.

        Parameters
        ----------
        mask : int
            Bitmask of the jobs considered.

        Returns
        -------
        int
            Lower bound for the total weighted tardiness of the jobs,
            possibly negative.
        """
        t = 0
        value = 0.0
        for job, mu in zip(self.sequence, self.multipliers, strict=True):
            if mask >> job.index & 1:
                t += job.p
                value += mu * (t - job.d)
        return ceil(value - TOL)
