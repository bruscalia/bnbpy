import math
from typing import Any, List

import pytest

from bnbpy.colgen import ColumnGenProblem, Master, MasterSol, PriceSol, Pricing
from bnbpy.search import BranchAndBound
from bnbpy.status import OptStatus


class DummyMaster(Master):
    def __init__(self, initial_cost: float):
        self.cost = initial_cost
        self.duals = [1.0, 1.0]  # Arbitrary initial dual values
        self.num_cols = 0  # Count of columns added

    def add_col(self, _: Any) -> bool:
        """Simulate adding a column and decreasing the cost."""
        self.num_cols += 1
        # Each new column reduces the cost according to the rule
        self.cost -= 0.1**self.num_cols
        return True

    def solve(self) -> MasterSol:
        """Return the current cost and duals."""
        return MasterSol(cost=self.cost, duals=self.duals)


class DummyPricing(Pricing):
    def __init__(self, initial_red_cost: float = -5.0):
        super().__init__(price_tol=1e-2)
        # After this many rounds, reduced cost becomes non-negative
        self.round = 0  # Tracks the number of rounds executed
        self.depth = 0
        self.initial_red_cost = initial_red_cost

    def set_weights(self, c: Any):
        """Set weights based on the duals provided by the master problem."""
        pass  # In this dummy problem, weights have no effect

    def solve(self) -> PriceSol:
        """Return a column with reduced cost or stop if beyond decay rounds."""
        # Calculate reduced cost as it decays
        red_cost = self.initial_red_cost + (0.5 * self.round)
        self.round += 1
        self.depth += 1
        return PriceSol(
            red_cost=red_cost, new_col=f'col{self.round}|{self.depth}'
        )


class DummyColumnGenProblem(ColumnGenProblem):
    feas_tol = 0.1

    def __init__(
        self,
        initial_cost: float,
        initial_red_cost: float,
        max_iter_price: int = 100,
    ):
        master = DummyMaster(initial_cost=initial_cost)
        pricing = DummyPricing(initial_red_cost=initial_red_cost)
        super().__init__(
            master=master, pricing=pricing, max_iter_price=max_iter_price
        )

    def branch(self) -> List['DummyColumnGenProblem'] | None:
        c1 = self.copy()
        c2 = self.copy()
        c1.master.cost = self.master.cost + 3.9
        c2.master.cost = self.master.cost + 3.8
        return [c1, c2]

    def is_feasible(self) -> bool:
        print("Is feasible", self.master.cost % 2.7 <= self.feas_tol)
        return self.master.cost % 2.7 <= self.feas_tol

    def copy(self):
        other = super().copy(deep=False)
        other.pricing.round = 0
        return other


@pytest.mark.colgen
class TestColGen:
    basic_res = (19.88, 10, 0.5)

    @staticmethod
    @pytest.mark.parametrize(
        ('initial_cost', 'initial_red_cost', 'max_iter_price', 'res'),
        [(20, -5, 100, (19.88, 10, 0.5)), (23, -6, 100, (22.88, 12, 0.5))],
    )
    def test_conlgen(
        initial_cost: float,
        initial_red_cost: float,
        max_iter_price: int,
        res: tuple,
    ):
        # Create the dummy column generation problem
        problem = DummyColumnGenProblem(
            initial_cost=initial_cost,
            initial_red_cost=initial_red_cost,
            max_iter_price=max_iter_price,
        )
        # Calculate the bound using the dummy problem
        bound = problem.calc_bound()

        assert math.isclose(
            bound, res[0], abs_tol=1e-2
        ), 'Wrong CG dummy bound'
        assert (
            problem.master.num_cols == res[1]
        ), 'Wrong number of columns in CG dummy solve'
        assert (
            problem.pricing.solve().red_cost == res[2]
        ), 'Wrong result for pricing dummy problem'

    @staticmethod
    @pytest.mark.parametrize(
        (
            'initial_cost',
            'initial_red_cost',
            'max_iter_price',
            'maxiter',
            'res',
        ),
        [
            (20, -5, 100, 5, (OptStatus.INFEASIBLE, None, 19.88)),
            (13, -6, 100, 10, (OptStatus.FEASIBLE, 43.28, 12.88)),
            (13, -6, 100, 100, (OptStatus.OPTIMAL, 24.38, 24.38)),
        ],
    )
    def test_bnp(
        initial_cost: float,
        initial_red_cost: float,
        max_iter_price: int,
        maxiter: int,
        res: tuple,
    ):
        # Create the dummy column generation problem
        problem = DummyColumnGenProblem(
            initial_cost=initial_cost,
            initial_red_cost=initial_red_cost,
            max_iter_price=max_iter_price,
        )
        bnb = BranchAndBound()
        sol = bnb.solve(problem, maxiter=maxiter)
        print(sol)
        assert sol.status == res[0], 'Wrong status after B&P'
        if res[1] is None:
            assert sol.cost == float('inf'), 'Wrong cost for unsolved problem'
        else:
            assert math.isclose(
                sol.cost, res[1], abs_tol=1e-1
            ), 'Wrong cost (ub) in B&P'
        assert math.isclose(
            sol.lb, res[2], abs_tol=1e-1
        ), f'Wrong LB in B&P {sol.lb}'

    @staticmethod
    def test_copy():
        problem = DummyColumnGenProblem(
            initial_cost=20,
            initial_red_cost=-5,
            max_iter_price=100,
        )
        other = problem.copy()
        assert problem.pricing is not other.pricing, 'Pricing is the same'
        assert (
            problem.pricing.solutions is not other.pricing.solutions
        ), 'Pricing solutions are the same'
        for _ in range(len(problem.pricing.solutions)):
            a = problem.pricing.solutions.pop()
            b = problem.pricing.solutions.pop()
            assert a is b, "Solutions don't share mem loc in Pricing"
