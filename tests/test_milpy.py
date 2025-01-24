import numpy as np
import pytest

from bnbprob.milpy.problem import MILP
from bnbpy import BestFirstBnB, BreadthFirstBnB, DepthFirstBnB
from bnbpy.status import OptStatus

np.random.seed(42)


@pytest.mark.milp
@pytest.mark.milpnaive
class TestNaive:
    c = np.array([-5.0, -4.0])

    A_ub = np.array([[2.0, 3.0], [2.0, 1.0]])
    b_ub = np.array([12.0, 6.0])
    cost = -18.0
    x_sol = np.array([2.0, 2.0])

    @pytest.mark.parametrize(
        'bnb_class', [BestFirstBnB, BreadthFirstBnB, DepthFirstBnB]
    )
    def test_milp(self, bnb_class):
        milp = MILP(self.c, A_ub=self.A_ub, b_ub=self.b_ub)
        bnb = bnb_class(eval_node='in')
        bnb.solve(milp)
        self.assert_cost(bnb.solution.cost)
        self.assert_sol(bnb.solution.x)

    def assert_cost(self, cost: float):
        assert np.isclose(
            cost, self.cost, atol=1e-4
        ), f'Wrong cost for MILP test {cost}, expected {self.cost}'

    def assert_sol(self, x: np.ndarray):
        assert np.allclose(
            x, self.x_sol, atol=1e-4
        ), f'Wrong x for MILP test {x}, expected {self.x_sol}'


@pytest.mark.milp
@pytest.mark.knapsack
class TestKnapsack:
    N = 10

    # Weight associated with each item
    w = np.random.normal(loc=5.0, scale=1.0, size=N).clip(0.5, 10.0)
    v = np.random.normal(loc=6.0, scale=2.0, size=N).clip(0.5, 10.0)

    # Price associated with each item
    c = -np.random.normal(loc=10.0, scale=1.0, size=N).clip(0.5, 20.0)

    # knapsack capacity
    kw = 21.0
    kv = 22.0

    A_ub = np.atleast_2d([w, v])
    b_ub = np.array([kw, kv])

    # Results
    cost = -41.726493076490556
    x_sol = np.array([1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0])

    @pytest.mark.parametrize(
        'bnb_class', [BestFirstBnB, BreadthFirstBnB, DepthFirstBnB]
    )
    def test_knapsack(self, bnb_class):
        milp = MILP(self.c, A_ub=self.A_ub, b_ub=self.b_ub, bounds=(0.0, 1.0))
        bnb = bnb_class(eval_node='in')
        bnb.solve(milp)
        self.assert_cost(bnb.solution.cost)
        self.assert_sol(bnb.solution.x)

    @pytest.mark.parametrize(
        ('status', 'eval_node', 'maxiter', 'explored'),
        [
            (OptStatus.OPTIMAL, 'in', 250, 125),
            (OptStatus.FEASIBLE, 'in', 11, 11),
            (OptStatus.RELAXATION, 'in', 0, 1),
            (OptStatus.OPTIMAL, 'out', 250, 71),
            (OptStatus.FEASIBLE, 'out', 11, 11),
            (OptStatus.RELAXATION, 'out', 0, 1),
        ],
    )
    def test_status_ks(self, status, eval_node, maxiter, explored):
        milp = MILP(self.c, A_ub=self.A_ub, b_ub=self.b_ub, bounds=(0.0, 1.0))
        bnb = DepthFirstBnB(eval_node=eval_node)
        bnb.solve(milp, maxiter=maxiter)
        assert (
            bnb.solution.status == status
        ), f'Wrong status for ks test {bnb.solution.status}, expected {status}'
        assert (
            bnb.explored == explored
        ), (
            'Wrong number of nodes explored in ks test'
            f' {bnb.explored}, expected {explored}'
        )

    def assert_cost(self, cost: float):
        assert np.isclose(
            cost, self.cost, atol=1e-4
        ), f'Wrong cost for ks test {cost}, expected {self.cost}'

    def assert_sol(self, x: np.ndarray):
        assert np.allclose(
            x, self.x_sol, atol=1e-4
        ), f'Wrong x for ks test {x}, expected {self.x_sol}'
