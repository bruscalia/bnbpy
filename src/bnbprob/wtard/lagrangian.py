"""
Lagrangian lower bound for 1 || sum w_j T_j (Potts and Van Wassenhove,
1985).

Relaxing the constraints T_j >= C_j - d_j with multipliers
0 <= u_j <= w_j leaves the problem

    L(u) = min  sum_j u_j C_j - sum_j u_j d_j

solved exactly by the WSPT rule with weights u_j. Given a heuristic
sequence, the multiplier adjustment method chooses the multipliers that
maximize L(u) among those for which the sequence is WSPT optimal, i.e.,
u_j / p_j is nonincreasing along it. In that case L(u) = sum_j u_j L_j,
in which L_j is the lateness of job j in the sequence.

The solution is given in closed form (Theorem 1): with the prefix sums
S_j = sum_{i <= j} p_i L_i, let v_1 < v_2 < ... be the positions in which
S_j reaches a new maximum above S_0 = 0. Jobs in (v_{k-1}, v_k] share the
ratio u_j / p_j = min_{h <= v_k} w_h / p_h, and jobs after the last record
get null multipliers, so the bound is computed in a single pass.
"""

from dataclasses import dataclass
from math import ceil, inf
from typing import Iterable, NamedTuple, TypeVar

from .problem import WeightedTardiness
from .state import Job, ProblemState

TOL = 1e-9
"""Tolerance for rounding up fractional bounds."""

L = TypeVar('L', bound='LagrangianTardiness')


class Bounds(NamedTuple):
    lower: int
    """Lagrangian bound of the multiplier adjustment method."""
    upper: int
    """Total weighted tardiness of the sequence."""


def multiplier_adjustment(sequence: Iterable[Job]) -> Bounds:
    """Lower and upper bounds from a sequence of jobs processed from time
    zero (Potts and Van Wassenhove, 1985, Theorem 1).

    Parameters
    ----------
    sequence : Iterable[Job]
        Heuristic sequence of jobs.

    Returns
    -------
    Bounds
        Best Lagrangian bound among the multipliers for which the sequence
        is WSPT optimal, and the total weighted tardiness of the sequence.
    """
    t = 0
    prefix = 0  # S_j
    record = 0  # S_{v_{k-1}}
    ratio = inf  # min_{h <= j} w_h / p_h
    lower = 0.0
    upper = 0
    for job in sequence:
        t += job.p
        upper += job.w * max(t - job.d, 0)
        # Jobs without processing time get null multipliers
        if not job.p:
            continue
        prefix += job.p * (t - job.d)
        ratio = min(ratio, job.w / job.p)
        if prefix > record:
            lower += ratio * (prefix - record)
            record = prefix
    return Bounds(lower=ceil(lower - TOL), upper=upper)


@dataclass(slots=True)
class Reference:
    """Best known sequence of all jobs, shared among nodes."""

    sequence: list[Job]
    cost: int


class LagrangianTardiness(WeightedTardiness):
    """Total weighted tardiness problem 1 || sum w_j T_j with the
    Lagrangian bound of Potts and Van Wassenhove (1985).

    Branching and dominance follow ``WeightedTardiness``. At each node, the
    multipliers are adjusted to the best known sequence restricted to the
    unscheduled jobs, which completed by the fixed jobs is also a feasible
    solution. The best known sequence starts from the ATC warmstart and is
    replaced whenever a node completes it at a lower cost. Use
    ``TardinessLagrangianSearch`` to also update the incumbent of the
    search with these solutions.
    """

    _reference: Reference
    """
    Best known sequence, used to adjust the multipliers of every node.
    """
    _improved: bool
    """
    Whether completing the node by the reference sequence improved it.
    """

    def __init__(self, state: ProblemState) -> None:
        super().__init__(state)
        sequence = self._best_atc_sequence()
        self._reference = Reference(sequence, self._sequence_cost(sequence))
        self._improved = False

    def calc_bound(self) -> int:
        state = self.state
        bounds = multiplier_adjustment(self._reference_remaining())
        cost = state.fixed_cost + bounds.upper
        self._improved = cost < self._reference.cost
        if self._improved:
            self._reference.sequence = (
                self._reference_remaining() + state.fixed[::-1]
            )
            self._reference.cost = cost
        return state.fixed_cost + bounds.lower

    def primal_heuristic(self) -> 'LagrangianTardiness | None':
        """Completes the sequence of unscheduled jobs by the reference
        sequence, if it improved the best known solution in the last
        bound computation.

        Returns
        -------
        LagrangianTardiness | None
            Copy of the problem with all jobs fixed, or None
        """
        if not self._improved:
            return None
        sol = self.child_copy(deep=False)
        # Jobs are fixed backwards, so the last job comes first
        for job in reversed(self._reference_remaining()):
            sol._fix_job(sol.state.remaining.index(job))
        return sol

    def child_copy(self: L, deep: bool = False) -> L:
        other = super().child_copy(deep)
        other._improved = False
        return other

    def _reference_remaining(self) -> list[Job]:
        """Unscheduled jobs in the order of the reference sequence."""
        mask = self.state.remaining_mask
        return [
            job for job in self._reference.sequence if mask >> job.index & 1
        ]
