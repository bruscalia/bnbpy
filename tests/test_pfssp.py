import random

import pytest

from bnbprob.pfssp.bnb import LazyBnB
from bnbprob.pfssp.cython.problem import PermFlowShop, PermFlowShop2M
from bnbprob.pfssp.pypure.problem import PermFlowShop as PyPermFlowShop
from bnbpy import BestFirstBnB, BranchAndBound, DepthFirstBnB


@pytest.mark.pfssp
class TestPFSSP:
    J = 10
    M = 4
    p_choices = list(range(5, 25))
    sol_value = 182
    nodes = 11

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
            (DepthFirstBnB, PermFlowShop, 'out', 182, 27, 'quick'),
            (BestFirstBnB, PermFlowShop, 'out', 182, 17, 'quick'),
            (DepthFirstBnB, PermFlowShop, 'in', 182, 0, 'neh'),
            (BestFirstBnB, PermFlowShop, 'in', 182, 0, 'neh'),
            (DepthFirstBnB, PermFlowShop, 'out', 182, 0, 'neh'),
            (BestFirstBnB, PermFlowShop, 'out', 182, 0, 'neh'),
            (DepthFirstBnB, PyPermFlowShop, 'in', 182, 11, 'quick'),
            (BestFirstBnB, PyPermFlowShop, 'in', 182, 11, 'quick'),
            (DepthFirstBnB, PyPermFlowShop, 'out', 182, 27, 'quick'),
            (BestFirstBnB, PyPermFlowShop, 'out', 182, 17, 'quick'),
            (DepthFirstBnB, PyPermFlowShop, 'in', 182, 0, 'neh'),
            (BestFirstBnB, PyPermFlowShop, 'in', 182, 0, 'neh'),
            (DepthFirstBnB, PyPermFlowShop, 'out', 182, 0, 'neh'),
            (BestFirstBnB, PyPermFlowShop, 'out', 182, 0, 'neh'),
        ],
    )
    def test_res_pfssp(  # noqa: PLR0913, PLR0917
        self, bnb_cls, prob_cls, eval_node, cost, explored, constructive
    ):
        problem = self.start_problem(prob_cls, constructive=constructive)
        bnb = bnb_cls(eval_node=eval_node)
        bnb.solve(problem)
        cost_sol = bnb.solution.cost
        assert (
            cost_sol == cost
        ), f'Wrong cost for FSSP {bnb_cls} {cost_sol}, expected {cost}'
        assert bnb.explored == explored, (
            f'Wrong number of nodes explored for FSSP {bnb_cls}'
            f' {bnb.explored}, expected {explored}'
        )

    def start_problem(self, cls, **kwargs):
        random.seed(42)
        p = [
            [random.choice(self.p_choices) for _ in range(self.M)]
            for _ in range(self.J)
        ]
        problem = cls.from_p(p, **kwargs)
        return problem

    def test_warmstart(self):
        problem = self.start_problem(PermFlowShop2M, constructive='quick')
        bnb = DepthFirstBnB(eval_node='in')
        bnb.solve(problem)
        cost = bnb.solution.cost
        assert (
            bnb.solution.cost == self.sol_value
        ), f'Wrong solution for DFS {cost}, expected {self.sol_value}'
        assert bnb.explored == self.nodes, (
            f'Wrong number of explored nodes for DFS {bnb.explored},'
            f' expected {self.nodes}'
        )

    @pytest.mark.parametrize('cls', [PermFlowShop, PyPermFlowShop])
    def test_lazy(self, cls):
        problem = self.start_problem(cls, constructive='quick')
        bnb = BranchAndBound(eval_node='in')
        bnb.solve(problem)
        bnblazy = LazyBnB(eval_node='in')
        problem_lazy = self.start_problem(cls)
        bnblazy.solve(problem_lazy)
        base_cost = bnb.solution.cost
        cb_cost = self.sol_value
        assert (
            bnb.solution.cost == bnblazy.solution.cost
        ), f'Wrong solution for CB {base_cost}, expected {cb_cost}'
        assert bnb.explored == self.nodes, (
            f'Wrong number of explored nodes for CB {bnblazy.explored},'
            f' expected {self.nodes}'
        )

    @staticmethod
    def test_neh():
        p = [
            [5, 9, 8, 10, 1],
            [9, 3, 10, 1, 8],
            [9, 4, 5, 8, 6],
            [4, 8, 8, 7, 2],
        ]
        res = 54
        problem = PermFlowShop.from_p(p, constructive='neh')
        sol = problem.warmstart()
        cost = sol.calc_lb_1m()
        assert cost == res, f'Wrong result for neh {cost} vs 54 (expected)'


@pytest.mark.pfssp
class TestPFSSPBounds:
    p = [[5, 9, 7, 4], [9, 3, 3, 8], [8, 10, 5, 6], [1, 8, 6, 2]]

    res_root = (39, 42)
    res_first = [
        (43, 43),
        (47, 47),
        (46, 46),
        (42, 42),
    ]

    res_final = 43

    def test_root(self):
        problem = PermFlowShop.from_p(self.p)
        lb1 = problem.solution.perm.lower_bound_1m()
        lb5 = problem.solution.perm.lower_bound_2m()
        assert (
            (
                lb1,
                lb5,
            )
            == self.res_root
        ), (
            f'Wrong root lower bounds for toy problem: {(lb1, lb5)};'
            f' expected {self.res_root}'
        )

    @pytest.mark.parametrize('j', [0, 1, 2, 3])
    def test_first_level(self, j):
        problem = PermFlowShop.from_p(self.p)
        problem.solution.perm.push_job(j)
        lb1 = problem.solution.perm.lower_bound_1m()
        lb5 = problem.solution.perm.lower_bound_2m()
        res = self.res_first[j]
        assert (
            (
                lb1,
                lb5,
            )
            == res
        ), (
            f'Wrong root lower bounds for toy problem: {(lb1, lb5)};'
            f' expected {res}'
        )
