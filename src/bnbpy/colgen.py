import copy
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional, Set

from bnbpy.problem import Problem

log = logging.getLogger(__name__)

LARGE_INT = 100000000


@dataclass
class PriceSol:
    """Returns the solutions of the pricing problem
    (which includes a new column). Is is NOT recommended to modify
    these instance after creation due to safe hashing.
    """

    red_cost: float
    new_col: Any

    def __hash__(self):
        return hash(str(self.new_col))

    def __eq__(self, value: object) -> bool:
        return str(self) == str(value)


@dataclass
class MasterSol:
    """Returns the solutions of the master problem
    (which includes dual information). Is is NOT recommended to modify
    these instance after creation due to safe hashing.
    """
    cost: float
    duals: Any

    def __hash__(self):
        return hash(str(self))


class Pricing(ABC):
    """Abstraction for pricing problem"""

    price_tol: float
    """Tolerance for including new columns into master problem"""
    solutions: Set[PriceSol]
    """Solutions to price problems already returned"""

    def __init__(self, price_tol=1e-2):
        self.price_tol = price_tol
        self.solutions = set()

    @abstractmethod
    def set_weights(self, c: Any):
        """Modifies problem by incorporating new weights

        Parameters
        ----------
        c : Any
            New weights (depend on problem structure)
        """
        pass

    @abstractmethod
    def solve(self) -> PriceSol:
        """Solves pricing problem and returns `PriceSol` instance

        Returns
        -------
        PriceSol
            Instance with reduced cost and new column
        """
        pass

    def evaluate(self) -> Optional[PriceSol]:
        """
        Solves pricing problem and evaluates quality
        of solution by reduced cost and repeated solutions.
        Only returns columns not yet generated.
        """
        sol_price = self.solve()
        if (
            sol_price.red_cost < -self.price_tol
            and sol_price not in self.solutions
        ):
            self.solutions.add(sol_price)
            return sol_price

    def copy(self, deep=False):
        if deep:
            return copy.deepcopy(self)
        child = copy.copy(self)
        child.solutions = copy.copy(self.solutions)
        return child


class Master(ABC):
    """Abstraction of master problem
    Must overwrite methods `add_col` and `solve`
    """

    @abstractmethod
    def add_col(self, c: Any) -> bool:
        """Includes new column into master problem
        and returns `True` if it is valid to continue pricing

        Parameters
        ----------
        c : Any
            New column

        Returns
        -------
        bool
            Either or not to proceed
        """
        pass

    @abstractmethod
    def solve(self) -> MasterSol:
        """Solves master problem and returns an instance of `MasterSol`

        Returns
        -------
        MasterSol
            Solution with cost and duals
        """
        pass

    def copy(self, deep=False):
        if deep:
            return copy.deepcopy(self)
        return copy.copy(self)


class ColumnGenProblem(Problem):
    """Abstraction of optimization problem solved using column generation"""

    master: Master
    pricing: Pricing

    def __init__(
        self,
        master: Master,
        pricing: Pricing,
        max_iter_price: Optional[int] = None,
    ):
        """Instantiate Column Generation Problem

        Parameters
        ----------
        master : Master
            Master problem (see `bnbpy.colgen.Master`)

        pricing : Pricing
            Pricing problem (see `bnbpy.colgen.Pricing`)

        max_iter_price : Optional[int], optional
            Maximum number of pricing iterations at node relaxation,
            by default None
        """
        super().__init__()
        if max_iter_price is None:
            max_iter_price = LARGE_INT
        self.max_iter_price = max_iter_price
        self.master = master
        self.pricing = pricing

    def cleanup(self):
        super().cleanup()
        self.master = None
        self.pricing = None

    def calc_bound(self):
        sol_master = self._calc_bound()
        return sol_master.cost

    def _calc_bound(self) -> MasterSol:
        """Basic loop scheme for computing lower bounds with pricing
        in case additional checks are desired

        Returns
        -------
        MasterSol
            Solution of master problem
        """
        for _ in range(self.max_iter_price):
            sol_master = self.master.solve()
            self.pricing.set_weights(sol_master.duals)
            sol_price = self.pricing.evaluate()
            if sol_price is None:
                break
            if not self.master.add_col(sol_price.new_col):
                break
        if sol_master.cost is not None:
            log.debug(f'Price finished: {sol_master.cost:.2f}')
        return sol_master

    def copy(self, deep=False):
        if deep:
            return super().copy(deep=True)
        child = copy.copy(self)
        child.solution = self.solution.copy(deep=False)
        child.pricing = self.pricing.copy()
        child.master = copy.copy(self.master)
        return child
