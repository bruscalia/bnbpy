import random

import pytest

from bnbprob.pfssp import LazyBnB, PermFlowShop, PermFlowShopLazy
from bnbpy import BestFirstBnB, BranchAndBound, DepthFirstBnB


@pytest.mark.pfssp
class TestPFSSP:
    J = 10
    M = 4
    p_choices = list(range(5, 25))
    sol_value = 182
    nodes = 11

    @pytest.mark.parametrize(
        ('bnb_cls', 'eval_node', 'cost', 'explored', 'constructive'),
        [
            (DepthFirstBnB, 'in', 182, 11, 'quick'),
            # (BreadthFirstBnB, 'in', 182, 11),
            (BestFirstBnB, 'in', 182, 11, 'quick'),
            (DepthFirstBnB, 'out', 182, 27, 'quick'),
            # (BreadthFirstBnB, 'out', 182, 11),
            (BestFirstBnB, 'out', 182, 20, 'quick'),
            (DepthFirstBnB, 'in', 182, 1, 'neh'),
            # (BreadthFirstBnB, 'in', 182, 11),
            (BestFirstBnB, 'in', 182, 1, 'neh'),
            (DepthFirstBnB, 'out', 182, 1, 'neh'),
            # (BreadthFirstBnB, 'out', 182, 11),
            (BestFirstBnB, 'out', 182, 1, 'neh'),
        ],
    )
    def test_res_pfssp(self, bnb_cls, eval_node, cost, explored, constructive):
        problem = self.start_problem(PermFlowShop, constructive=constructive)
        bnb = bnb_cls(eval_node=eval_node)
        bnb.solve(problem)
        cost_sol = bnb.solution.cost
        assert (
            cost_sol == cost
        ), f'Wrong cost for FSSP {bnb_cls} {cost_sol}, expected {cost}'
        assert (
            bnb.explored == explored
        ), (
            f'Wrong number of nodes explored for FSSP {bnb_cls}'
            f' {bnb.explored}, expected {explored}'
        )

    def start_problem(self, cls, **kwargs):
        random.seed(42)
        p = [
            [
                random.choice(self.p_choices)
                for _ in range(self.M)
            ]
            for _ in range(self.J)
        ]
        problem = cls.from_p(p, **kwargs)
        return problem

    def test_warmstart(self):
        problem = self.start_problem(PermFlowShop, constructive='quick')
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

    def test_lazy(self):
        problem = self.start_problem(PermFlowShop, constructive='quick')
        bnb = BranchAndBound(eval_node='in')
        bnb.solve(problem)
        bnblazy = LazyBnB(eval_node='in')
        problem_lazy = self.start_problem(PermFlowShopLazy)
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
            [4, 8, 8, 7, 2]
        ]
        res = 54
        problem = PermFlowShop.from_p(p, constructive='neh')
        sol = problem.warmstart()
        cost = sol.calc_bound()
        assert cost == res, f'Wrong result for neh {cost} vs 54 (expected)'
