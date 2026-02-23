import math
from typing import Any, List, cast

import pytest

from bnbpy.colgen import ColumnGenProblem, Master, MasterSol, PriceSol, Pricing
from bnbpy.cython.search import BranchAndBound
from bnbpy.cython.status import OptStatus


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
    def __init__(self, initial_red_cost: float = -2.0):
        super().__init__(price_tol=1e-2)
        self.round = 0  # Tracks the number of rounds executed
        self.initial_red_cost = initial_red_cost

    def set_weights(self, c: Any) -> None:
        """Set weights based on the duals provided by the master problem."""
        pass  # In this dummy problem, weights have no effect

    def solve(self) -> PriceSol:
        """Return a column with reduced cost or stop if beyond decay rounds."""
        # Optimized increment for balanced convergence
        red_cost = self.initial_red_cost + (0.5 * self.round)
        self.round += 1
        return PriceSol(red_cost=red_cost, new_col=f'col{self.round}')


class DummyColumnGenProblem(ColumnGenProblem):  # type: ignore
    feas_tol = 0.1
    master: DummyMaster
    pricing: DummyPricing

    def __init__(
        self,
        initial_cost: float,
        initial_red_cost: float = -2.0,  # Optimized default
        max_iter_price: int = 100,
    ):
        master = DummyMaster(initial_cost=initial_cost)
        pricing = DummyPricing(initial_red_cost=initial_red_cost)
        super().__init__(
            master=master, pricing=pricing, max_iter_price=max_iter_price
        )

    def branch(self) -> List['DummyColumnGenProblem']:
        c1 = self.copy()
        c2 = self.copy()
        c1.master.cost = self.master.cost + 3.7  # Optimized branching
        c2.master.cost = self.master.cost + 3.8
        return [c1, c2]

    def is_feasible(self) -> bool:
        return self.master.cost % 2.7 <= self.feas_tol

    def copy(self, deep: bool = False) -> 'DummyColumnGenProblem':
        other = cast(DummyColumnGenProblem, super().copy(deep=deep))
        # DON'T reset pricing.round - this was the main convergence issue!
        return other


@pytest.mark.colgen
class TestColGen:
    basic_res = (19.88, 10, 0.5)

    @staticmethod
    @pytest.mark.parametrize(
        ('initial_cost', 'initial_red_cost', 'max_iter_price', 'res'),
        [(20, -2, 100, (19.89, 4, 0.5)), (23, -2, 100, (22.89, 4, 0.5))],
    )
    def test_conlgen(
        initial_cost: float,
        initial_red_cost: float,
        max_iter_price: int,
        res: tuple[float, int, float],
    ) -> None:
        # Create the dummy column generation problem
        problem = DummyColumnGenProblem(
            initial_cost=initial_cost,
            initial_red_cost=initial_red_cost,
            max_iter_price=max_iter_price,
        )
        # Calculate the bound using the dummy problem
        bound = problem.calc_bound()

        assert math.isclose(bound, res[0], abs_tol=1e-2), (
            'Wrong CG dummy bound'
        )
        assert problem.master.num_cols == res[1], (
            'Wrong number of columns in CG dummy solve'
        )
        assert problem.pricing.solve().red_cost == res[2], (
            'Wrong result for pricing dummy problem'
        )

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
            (20, -2, 100, 5, (OptStatus.INFEASIBLE, None, 19.89)),
            (5, -6, 100, 50, (OptStatus.FEASIBLE, 27.09, 12.49)),
            (5, -6, 100, 100, (OptStatus.OPTIMAL, 16.29, 16.29)),
        ],
    )
    def test_bnp(
        initial_cost: float,
        initial_red_cost: float,
        max_iter_price: int,
        maxiter: int,
        res: tuple[OptStatus, float | None, float],
    ) -> None:
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
            assert math.isclose(sol.cost, res[1], abs_tol=1e-1), (
                f'Wrong cost (ub) in B&P {sol.cost} vs {res[1]}'
            )
        assert math.isclose(sol.lb, res[2], abs_tol=1e-1), (
            f'Wrong LB in B&P {sol.lb} vs {res[2]}'
        )

    @staticmethod
    def test_copy() -> None:
        problem = DummyColumnGenProblem(
            initial_cost=20,
            initial_red_cost=-2,
            max_iter_price=100,
        )
        other = problem.copy()
        assert problem.pricing is not other.pricing, 'Pricing is the same'
        assert problem.pricing.solutions is not other.pricing.solutions, (
            'Pricing solutions are the same'
        )
        for _ in range(len(problem.pricing.solutions)):
            a = problem.pricing.solutions.pop()
            b = problem.pricing.solutions.pop()
            assert a is b, "Solutions don't share mem loc in Pricing"
