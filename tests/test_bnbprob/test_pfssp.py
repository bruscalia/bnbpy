import random
from typing import Any, Type

import pytest

from bnbprob.pafssp.cython.bnb import LazyBnB
from bnbprob.pafssp.cython.problem import PermFlowShop
from bnbpy.cython.search import BestFirstBnB, BranchAndBound, DepthFirstBnB


@pytest.mark.pfssp
class TestPFSSP:
    J: int = 10
    M: int = 4
    p_choices: list[int] = list(range(5, 25))
    sol_value: int = 182
    nodes: int = 11

    @pytest.mark.parametrize(
        (
            'bnb_cls',
            'prob_cls',
            'eval_node',
            'cost',
            'explored',
            'constructive',
        ),
        [
            (DepthFirstBnB, PermFlowShop, 'in', 182, 11, 'quick'),
            (BestFirstBnB, PermFlowShop, 'in', 182, 11, 'quick'),
            (DepthFirstBnB, PermFlowShop, 'out', 182, 47, 'quick'),
            (BestFirstBnB, PermFlowShop, 'out', 182, 22, 'quick'),
            (DepthFirstBnB, PermFlowShop, 'in', 182, 0, 'neh'),
            (BestFirstBnB, PermFlowShop, 'in', 182, 0, 'neh'),
            (DepthFirstBnB, PermFlowShop, 'out', 182, 0, 'neh'),
            (BestFirstBnB, PermFlowShop, 'out', 182, 0, 'neh'),
        ],
    )
    def test_res_pfssp(  # noqa: PLR0913, PLR0917
        self,
        bnb_cls: Type[Any],
        prob_cls: Type[Any],
        eval_node: str,
        cost: int,
        explored: int,
        constructive: str,
    ) -> None:
        problem = self.start_problem(prob_cls, constructive=constructive)
        print(problem)
        bnb = bnb_cls(eval_node=eval_node)
        bnb.solve(problem)
        cost_sol = bnb.solution.cost
        assert cost_sol == cost, (
            f'Wrong cost for FSSP {bnb_cls} {cost_sol}, expected {cost}'
        )
        assert bnb.explored == explored, (
            f'Wrong number of nodes explored for FSSP {bnb_cls}'
            f' {bnb.explored}, expected {explored}'
        )

    def start_problem(self, cls: Type[Any], **kwargs: Any) -> Any:
        random.seed(42)
        p: list[list[int]] = [
            [random.choice(self.p_choices) for _ in range(self.M)]
            for _ in range(self.J)
        ]
        problem = cls.from_p(p, **kwargs)
        return problem

    def test_warmstart(self) -> None:
        problem = self.start_problem(PermFlowShop, constructive='quick')
        bnb = DepthFirstBnB(eval_node='in')
        bnb.solve(problem)
        cost: int = int(bnb.solution.cost)
        assert bnb.solution.cost == self.sol_value, (
            f'Wrong solution for DFS {cost}, expected {self.sol_value}'
        )
        assert bnb.explored == self.nodes, (
            f'Wrong number of explored nodes for DFS {bnb.explored},'
            f' expected {self.nodes}'
        )

    def test_lazy(
        self,
    ) -> None:
        problem = self.start_problem(PermFlowShop, constructive='quick')
        bnb = LazyBnB(delay_lb5=False)
        bnb.solve(problem)
        bnblazy = BranchAndBound(eval_node='in')
        problem_lazy = self.start_problem(PermFlowShop)
        bnblazy.solve(problem_lazy)
        base_cost: int = int(bnb.solution.cost)
        cb_cost: int = self.sol_value
        assert bnb.solution.cost == bnblazy.solution.cost, (
            f'Wrong solution for CB {base_cost}, expected {cb_cost}'
        )
        assert bnb.explored == self.nodes, (
            f'Wrong number of explored nodes for CB {bnblazy.explored},'
            f' expected {self.nodes}'
        )

    @staticmethod
    def test_neh() -> None:
        p: list[list[int]] = [
            [5, 9, 8, 10, 1],
            [9, 3, 10, 1, 8],
            [9, 4, 5, 8, 6],
            [4, 8, 8, 7, 2],
        ]
        res: int = 54
        problem = PermFlowShop.from_p(p, constructive='neh')
        sol = problem.warmstart()
        cost: int = sol.calc_lb_1m()
        assert cost == res, f'Wrong result for neh {cost} vs 54 (expected)'


@pytest.mark.pfssp
class TestPFSSPBounds:
    p: list[list[int]] = [
        [5, 9, 7, 4],
        [9, 3, 3, 8],
        [8, 10, 5, 6],
        [1, 8, 6, 2],
    ]

    res_root: tuple[int, int] = (39, 42)
    res_first: list[tuple[int, int]] = [
        (43, 43),
        (47, 47),
        (46, 46),
        (39, 42),
    ]

    res_final: int = 43

    def test_root(self) -> None:
        problem = PermFlowShop.from_p(self.p)
        lb1: int = problem.lower_bound_1m()
        lb5: int = problem.lower_bound_2m()
        assert (
            lb1,
            lb5,
        ) == self.res_root, (
            f'Wrong root lower bounds for toy problem: {(lb1, lb5)};'
            f' expected {self.res_root}'
        )

    @pytest.mark.parametrize('j', [0, 1, 2, 3])
    def test_first_level(self, j: int) -> None:
        problem = PermFlowShop.from_p(self.p)
        problem.push_job(j)
        lb1: int = problem.lower_bound_1m()
        lb5: int = problem.lower_bound_2m()
        res: tuple[int, int] = self.res_first[j]
        assert (
            lb1,
            lb5,
        ) == res, (
            f'Wrong root lower bounds for toy problem: {(lb1, lb5)};'
            f' expected {res}'
        )
