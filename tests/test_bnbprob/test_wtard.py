import random
from itertools import permutations
from math import ceil
from typing import Sequence, Type

import pytest
from scipy.optimize import linprog

from bnbprob.wtard import (
    Job,
    LagrangianTardiness,
    TardinessLagrangianSearch,
    WeightedTardiness,
    multiplier_adjustment,
    preemptive_bound,
)
from bnbpy import BestFirstBnB, BranchAndBound, BreadthFirstBnB, DepthFirstBnB

SEARCHES = [DepthFirstBnB, BreadthFirstBnB, BestFirstBnB]
PROBLEMS = [WeightedTardiness, LagrangianTardiness]
SOLVERS = [
    *[(WeightedTardiness, bnb_cls) for bnb_cls in SEARCHES],
    *[
        (LagrangianTardiness, bnb_cls)
        for bnb_cls in [*SEARCHES, TardinessLagrangianSearch]
    ],
]
SUBSET_PROB = 0.7
LP_TOL = 1e-6


def total_weighted_tardiness(
    sequence: Sequence[int], p: list[int], w: list[int], d: list[int]
) -> int:
    t = 0
    cost = 0
    for j in sequence:
        t += p[j]
        cost += w[j] * max(t - d[j], 0)
    return cost


def brute_force(p: list[int], w: list[int], d: list[int]) -> int:
    return min(
        total_weighted_tardiness(seq, p, w, d)
        for seq in permutations(range(len(p)))
    )


def slot_bound(jobs: list[Job], horizon: int) -> int:
    """Reference transportation relaxation: heaviest jobs first, each unit
    in the latest free slot not after its due date."""
    free = [True] * (horizon + 1)
    cost = 0
    for job in sorted(jobs, key=lambda job: -job.w):
        for _ in range(job.p):
            slot = min(job.d, horizon)
            while slot > 0 and not free[slot]:
                slot -= 1
            if slot > 0:
                free[slot] = False
            else:
                cost += job.w
    return cost


def random_instance(
    rng: random.Random, n: int
) -> tuple[list[int], list[int], list[int]]:
    # Narrow ranges to produce ties and dominance relations
    p = [rng.randint(1, 6) for _ in range(n)]
    w = [rng.randint(1, 4) for _ in range(n)]
    total = sum(p)
    d = [rng.randint(0, total) for _ in range(n)]
    return p, w, d


@pytest.mark.wtard
class TestPinedoExample:
    """Example 3.6.3 in Pinedo (2008)."""

    problem_cls: Type[WeightedTardiness] = WeightedTardiness
    p = [12, 8, 15, 9]
    w = [4, 5, 3, 5]
    d = [16, 26, 25, 27]
    dominated = [1 << 2, 1 << 3, 0, 0]
    child_bounds = {2: 65, 3: 112}
    ws_value = 67
    ws_sequence = [0, 1, 3, 2]
    sol_value = 67
    sol_sequence = [0, 1, 3, 2]

    @pytest.fixture
    def problem(self) -> WeightedTardiness:
        return self.problem_cls.from_data(self.p, self.w, self.d)

    def test_dominance(self, problem: WeightedTardiness) -> None:
        jobs = sorted(problem.state.remaining, key=lambda job: job.index)
        assert [job.dominated for job in jobs] == self.dominated

    def test_root_children(self, problem: WeightedTardiness) -> None:
        children = problem.branch()
        bounds = {
            child.state.fixed[0].index: child.calc_bound()
            for child in children
        }
        assert bounds == self.child_bounds

    def test_warmstart(self, problem: WeightedTardiness) -> None:
        ws = problem.warmstart()
        sequence = [job.index for job in ws.sequence]
        assert ws.is_feasible()
        assert sequence == self.ws_sequence
        assert ws.calc_bound() == self.ws_value
        # The original problem is untouched
        assert not problem.state.fixed

    @pytest.mark.parametrize('bnb_cls', SEARCHES)
    def test_solve(
        self,
        problem: WeightedTardiness,
        bnb_cls: Type[BranchAndBound[WeightedTardiness]],
    ) -> None:
        res = bnb_cls(problem, eval_node='in').solve()
        sequence = [job.index for job in res.problem.sequence]
        assert res.solution.cost == self.sol_value
        assert sequence == self.sol_sequence


@pytest.mark.wtard
class TestPinedoExampleLagrangian(TestPinedoExample):
    problem_cls = LagrangianTardiness
    child_bounds = {2: 57, 3: 96}


@pytest.mark.wtard
@pytest.mark.parametrize('seed', range(20))
def test_bound_matches_slot_relaxation(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(50):
        p, w, d = random_instance(rng, rng.randint(1, 8))
        jobs = [
            Job(index=j, p=p[j], w=w[j], d=d[j])
            for j in range(len(p))
            if rng.random() < SUBSET_PROB
        ]
        horizon = sum(job.p for job in jobs)
        jobs.sort(key=lambda job: job.d)
        assert preemptive_bound(jobs, horizon) == slot_bound(jobs, horizon)


def lagrangian_lp(sequence: list[Job]) -> float:
    """Best value of sum u_j L_j for multipliers 0 <= u_j <= w_j with
    u_j / p_j nonincreasing along the sequence."""
    jobs = [job for job in sequence if job.p]
    if not jobs:
        return 0.0
    lateness = []
    t = 0
    for job in jobs:
        t += job.p
        lateness.append(t - job.d)
    rows = []
    for k in range(len(jobs) - 1):
        row = [0.0] * len(jobs)
        row[k] = -1 / jobs[k].p
        row[k + 1] = 1 / jobs[k + 1].p
        rows.append(row)
    res = linprog(
        [-lk for lk in lateness],
        A_ub=rows or None,
        b_ub=[0.0] * len(rows) or None,
        bounds=[(0, job.w) for job in jobs],
    )
    return float(-res.fun)


@pytest.mark.wtard
@pytest.mark.parametrize('seed', range(20))
def test_multiplier_adjustment_optimal(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(20):
        p, w, d = random_instance(rng, rng.randint(1, 8))
        # Include jobs without processing time
        p = [0 if rng.random() > SUBSET_PROB else pj for pj in p]
        jobs = [Job(index=j, p=p[j], w=w[j], d=d[j]) for j in range(len(p))]
        rng.shuffle(jobs)
        bounds = multiplier_adjustment(jobs)
        sequence = [job.index for job in jobs]
        assert bounds.lower == ceil(lagrangian_lp(jobs) - LP_TOL)
        assert bounds.upper == total_weighted_tardiness(sequence, p, w, d)


@pytest.mark.wtard
def test_lagrangian_unit_jobs() -> None:
    # Transportation bound is n, but every job is late by its completion
    n = 10
    p, w, d = [1] * n, [1] * n, [0] * n
    assert WeightedTardiness.from_data(p, w, d).calc_bound() == n
    lagrangian = LagrangianTardiness.from_data(p, w, d)
    assert lagrangian.calc_bound() == n * (n + 1) // 2


@pytest.mark.wtard
@pytest.mark.parametrize('problem_cls', PROBLEMS)
def test_solve_again_after_clean_cache(
    problem_cls: Type[WeightedTardiness],
) -> None:
    p, w, d = random_instance(random.Random(0), 7)
    problem = problem_cls.from_data(p, w, d)
    first = DepthFirstBnB(problem, eval_node='in').solve()
    problem.clean_cache()
    second = DepthFirstBnB(problem, eval_node='in').solve()
    assert first.solution.cost == second.solution.cost == brute_force(p, w, d)


@pytest.mark.wtard
@pytest.mark.parametrize('seed', range(20))
@pytest.mark.parametrize(('problem_cls', 'bnb_cls'), SOLVERS)
def test_optimal_random(
    seed: int,
    problem_cls: Type[WeightedTardiness],
    bnb_cls: Type[BranchAndBound[WeightedTardiness]],
) -> None:
    rng = random.Random(seed)
    p, w, d = random_instance(rng, rng.randint(1, 7))
    problem = problem_cls.from_data(p, w, d)
    assert problem.calc_bound() <= brute_force(p, w, d)
    res = bnb_cls(problem, eval_node='in').solve()
    sequence = [job.index for job in res.problem.sequence]
    assert sorted(sequence) == list(range(len(p)))
    assert res.solution.cost == brute_force(p, w, d)
    assert total_weighted_tardiness(sequence, p, w, d) == res.solution.cost
