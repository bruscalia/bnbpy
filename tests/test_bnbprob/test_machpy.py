import itertools
import random
from typing import Any, Type

import pytest

from bnbprob.machdeadline import (
    DeadlineLagrangianSearch,
    Job,
    LagrangianDeadline,
    MachDeadlineProb,
)
from bnbpy import BestFirstBnB, BreadthFirstBnB, DepthFirstBnB
from bnbpy.cython.status import OptStatus


class NoWarmstart(MachDeadlineProb):
    def warmstart(self) -> None:  # noqa: PLR6301
        return None


@pytest.mark.machdeadline
class TestMachDeadLine:
    p = [4, 3, 8, 2, 7, 6]
    w = [1, 1, 1, 1, 1, 1]
    d = [10, 20, 20, 30, 30, 30]
    sol_value = 86
    dfs_nodes = 3
    bfs_nodes = 9
    bb_nodes = 3

    @pytest.fixture
    def problem(self) -> MachDeadlineProb:  # noqa: PLR6301
        jobs = [
            Job(id=j, p=self.p[j], w=self.w[j], d=self.d[j])
            for j in range(len(self.p))
        ]
        problem = NoWarmstart(jobs)
        return problem

    def test_dfs(self, problem: MachDeadlineProb) -> None:
        bnb = DepthFirstBnB(problem, eval_node='in')
        bnb.solve()
        cost = bnb.solution.cost
        assert bnb.solution.cost == self.sol_value, (
            f'Wrong solution for DFS {cost}, expected {self.sol_value}'
        )
        assert bnb.explored == self.dfs_nodes, (
            f'Wrong number of explored nodes for DFS {bnb.explored},'
            f' expected {self.dfs_nodes}'
        )

    def test_bfs(self, problem: MachDeadlineProb) -> None:
        bnb = BreadthFirstBnB(problem, eval_node='in')
        bnb.solve()
        cost = bnb.solution.cost
        assert bnb.solution.cost == self.sol_value, (
            f'Wrong solution for BFS {cost}, expected {self.sol_value}'
        )
        assert bnb.explored == self.bfs_nodes, (
            f'Wrong number of explored nodes for BFS {bnb.explored},'
            f' expected {self.bfs_nodes}'
        )

    def test_bbs(self, problem: MachDeadlineProb) -> None:
        bnb = BestFirstBnB(problem, eval_node='in')
        bnb.solve()
        cost = bnb.solution.cost
        assert bnb.solution.cost == self.sol_value, (
            f'Wrong solution for lb priority {cost}, expected {self.sol_value}'
        )
        assert bnb.explored == self.bb_nodes, (
            f'Wrong number of explored nodes for lb priority'
            f' {bnb.explored}, expected {self.bb_nodes}'
        )


def brute_force(jobs: list[Job]) -> float:
    """Minimum weighted completion time meeting all deadlines."""
    best = float('inf')
    for perm in itertools.permutations(jobs):
        t = 0
        cost = 0
        for job in perm:
            t += job.p
            cost += job.w * t
            if t > job.d:
                break
        else:
            best = min(best, cost)
    return best


def random_jobs(seed: int, n: int = 6) -> list[Job]:
    rng = random.Random(seed)
    p = [rng.randint(1, 9) for _ in range(n)]
    total = sum(p)
    # Tight deadlines: some instances are infeasible
    return [
        Job(
            id=j, p=p[j], w=rng.randint(1, 5), d=rng.randint(total // 2, total)
        )
        for j in range(n)
    ]


@pytest.mark.machdeadline
@pytest.mark.integration
class TestMachDeadlineBruteForce:
    @staticmethod
    @pytest.mark.parametrize('eval_node', ['in', 'out', 'both'])
    @pytest.mark.parametrize(
        ('prob_cls', 'bnb_cls'),
        [
            (prob_cls, bnb_cls)
            for prob_cls in [NoWarmstart, MachDeadlineProb, LagrangianDeadline]
            for bnb_cls in [DepthFirstBnB, BreadthFirstBnB, BestFirstBnB]
        ]
        + [(LagrangianDeadline, DeadlineLagrangianSearch)],
    )
    def test_random_instances(
        prob_cls: Type[Any], bnb_cls: Type[Any], eval_node: str
    ) -> None:
        for seed in range(25):
            jobs = random_jobs(seed)
            opt = brute_force(jobs)
            res = bnb_cls(prob_cls(jobs), eval_node=eval_node).solve()
            assert res.cost == opt, f'seed {seed}: {res} (optimum {opt})'
            if opt == float('inf'):
                assert res.status == OptStatus.INFEASIBLE
            else:
                assert res.status == OptStatus.OPTIMAL
