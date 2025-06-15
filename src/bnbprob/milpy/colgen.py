import logging
import math
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple, Union, cast

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import OptimizeResult, linprog

from bnbprob.milpy.problem import MILP, MILPSol
from bnbprob.milpy.utils import BoundType
from bnbpy.colgen import (
    ColumnGenProblem,
    Master,
    MasterSol,
    Pricing,
)
from bnbpy.solution import Solution

log = logging.getLogger(__name__)


@dataclass
class MILPColumn:
    """New column create in set cover master problem"""

    a_ub: Optional[NDArray[np.float64]] = None
    """Column coefficients (1d array)"""
    a_eq: Optional[NDArray[np.float64]] = None
    """Column coefficients (1d array)"""
    c: Union[int, float] = 0.0
    """Column partial cost in obj function (minimize)"""
    bounds: BoundType = (0, None)
    """Column bounds (tuple - scipy compatible)"""

    def __hash__(self) -> int:
        return hash(str(self))


@dataclass
class MILPDuals:
    """Dual information of MILP problem solution"""

    lower: Optional[NDArray[np.float64]] = None
    """Duals of lower bounds"""
    upper: Optional[NDArray[np.float64]] = None
    """Duals of upper bounds"""
    eqlin: Optional[NDArray[np.float64]] = None
    """Duals of equality constraints"""
    ineqlin: Optional[NDArray[np.float64]] = None
    """Duals of inequality constraints"""

    def __hash__(self) -> int:
        return hash(str(self))


class MILPMaster(Master):
    """Master Problem (MILP)"""

    milp: MILP
    """MILP instance that defines master problem"""

    def __init__(self, milp: MILP):
        self.milp = milp

    @property
    def c(self) -> NDArray[np.float64]:
        return self.milp.c

    @c.setter
    def c(self, c: NDArray[np.float64]) -> None:
        self.milp.c = c

    @property
    def A_ub(self) -> NDArray[np.float64] | None:
        return self.milp.A_ub

    @A_ub.setter
    def A_ub(self, A_ub: NDArray[np.float64]) -> None:
        self.milp.A_ub = A_ub

    @property
    def A_eq(self) -> NDArray[np.float64] | None:
        return self.milp.A_eq

    @A_eq.setter
    def A_eq(self, A_eq: NDArray[np.float64]) -> None:
        self.milp.A_eq = A_eq

    @property
    def b_ub(self) -> NDArray[np.float64] | None:
        return self.milp.b_ub

    @b_ub.setter
    def b_ub(self, b_ub: NDArray[np.float64]) -> None:
        self.milp.b_ub = b_ub

    @property
    def b_eq(self) -> NDArray[np.float64] | None:
        return self.milp.b_eq

    @b_eq.setter
    def b_eq(self, b_eq: NDArray[np.float64]) -> None:
        self.milp.b_eq = b_eq

    @property
    def bounds(self) -> List[BoundType]:
        return self.milp.bounds

    @bounds.setter
    def bounds(self, bounds: List[BoundType]) -> None:
        self.milp.bounds = bounds

    def add_col(self, c: MILPColumn) -> bool:
        """Includes new column into problem
        and evaluates if pricing should proceed
        (considering cost and bounds).

        Parameters
        ----------
        c : SetCoverColumn
            New column to be included

        Returns
        -------
        bool
            Either or not to proceed column generation
        """
        valid = None
        if c.a_ub is not None:
            a_ub = c.a_ub.reshape(-1, 1)
            if not self._column_exists_ub(a_ub):
                self.A_ub = np.hstack((self.A_ub, a_ub))  # type: ignore
                valid = True
        if c.a_eq is not None:
            a_eq = c.a_eq.reshape(-1, 1)
            if not self._column_exists_eq(a_eq):
                self.A_eq = np.hstack((self.A_eq, a_eq))  # type: ignore
                valid = True
        if valid:
            self.c = np.append(self.c, c.c)
            self.bounds.append(c.bounds)
        return cast(bool, valid)

    def _column_exists_ub(self, a: NDArray[np.float64]) -> bool:
        matches = self.A_ub == a
        return cast(bool, np.any(np.all(matches, axis=0)))

    def _column_exists_eq(self, a: NDArray[np.float64]) -> bool:
        matches = self.A_eq == a
        return cast(bool, np.any(np.all(matches, axis=0)))

    def solve(self) -> MasterSol:
        """Solves Master Problem, returning solution with CG attributes
        and scipy results.

        Returns
        -------
        MasterSol
            Solution o the master problem (with duals)
        """
        self.milp.compute_bound()
        sol = self.milp.solution.scipy_res
        duals = MILPDuals(
            lower=sol.lower.marginals,  # type: ignore
            upper=sol.upper.marginals,  # type: ignore
            eqlin=sol.eqlin.marginals,  # type: ignore
            ineqlin=sol.ineqlin.marginals,  # type: ignore
        )
        return MasterSol(sol.fun, duals)  # type: ignore

    def solve_ineq_dual(self) -> OptimizeResult:
        """Backup for dual solution stabilization alternative

        Returns
        -------
        OptimizeResult
            Scipy results for a dual formulation of the set cover problem
        """
        if self.A_ub is None or self.b_ub is None:
            raise ValueError(
                'Master problem does not have valid A_ub or b_ub matrices.'
            )
        sol_dual = linprog(
            self.b_ub,
            A_ub=-self.A_ub.T,
            b_ub=self.c,
            bounds=(0, None),
        )
        return sol_dual


class ColGenMILP(ColumnGenProblem):
    """Column Generation Scheme with MILP Master Problem"""

    master: MILPMaster
    pricing: Pricing
    milp: MILP
    solution: MILPSol

    def __init__(  # noqa: PLR0913, PLR0917
        self,
        c: np.ndarray,
        A_ub: Optional[np.ndarray] = None,
        b_ub: Optional[np.ndarray] = None,
        A_eq: Optional[np.ndarray] = None,
        b_eq: Optional[np.ndarray] = None,
        bounds: Optional[Union[BoundType, List[BoundType]]] = None,
        integrality: Optional[Union[np.ndarray, int]] = None,
        pricing: Optional[Pricing] = None,
        max_iter_price: Optional[int] = None,
        branching: str = 'max',
        tol: float = 1e-4,
    ):
        """Instantiate Column Generation Problem with Set Cover Master Problem

        Parameters
        ----------
        c : np.ndarray
            Cost coefficients (minimization sense)

        A_ub : np.ndarray, optional
            Inequality matrix, by default None

        b_ub : np.ndarray, optional
            Inequality parameters, by default None

        A_eq : Optional[NDArray], optional
            Equality matrix, by default None

        b_eq : Optional[NDArray], optional
            Equality parameters, by default None

        bounds : Optional[Union[BoundType, List[BoundType]]], optional
            Bounds for decision variables,
            by default None

        integrality : Optional[Union[NDArray, int]], optional
            Integrality assignments (1 for integer, 0 otherwise),
            by default None

        pricing : Pricing, optional
            Pricing subproblem, by default None

        max_iter_price : Optional[int], optional
            Max number of iteration in pricing problem, by default None

        branching : str, optional
            Branching scheme in MILP, by default 'max'

        tol : float, optional
            Tolerance (gap) for MILP termination, by default 1e-4
        """
        assert isinstance(pricing, Pricing), (
            'Pricing must be valid instance of child class from `Pricing`'
        )
        self.milp = MILP(
            c,
            A_ub=A_ub,
            b_ub=b_ub,
            A_eq=A_eq,
            b_eq=b_eq,
            bounds=bounds,
            integrality=integrality,
            tol=tol,
            branching=branching,
        )
        master = MILPMaster(self.milp)
        super().__init__(master, pricing, max_iter_price)
        self.solution = self.milp.solution

    def set_solution(self, solution: Solution) -> None:
        self.milp.set_solution(solution)
        self.solution = self.milp.solution

    def is_feasible(self) -> bool:
        return self.milp.is_feasible()

    def branch(self) -> Optional[Sequence['ColGenMILP']]:
        # If not successful, just return
        if not self.solution.valid:
            self.solution.set_infeasible()
            return None

        # Choose branch var to define new limits
        i = self.milp.choose_branch_var()
        x_sol = self.solution.x
        if x_sol is None:
            raise ValueError('Solution x is None, cannot branch on it.')
        xi_lb = math.ceil(x_sol[i])
        xi_ub = math.floor(x_sol[i])

        # Instantiate and return the two child nodes
        p1 = self.copy()
        p1.update_bounds(i, (xi_lb, self.milp.bounds[i][-1]))
        p2 = self.copy()
        p2.update_bounds(i, (self.milp.bounds[i][0], xi_ub))
        return [p1, p2]

    def calc_bound(self) -> float:
        sol_master = self._calc_bound()
        lb = float('inf')
        if self.solution.valid:
            lb = math.ceil(round(sol_master.cost, 4))
        log.debug(f'Price finished: {lb:.2f}')
        return lb

    def update_bounds(
        self, i: int, bounds: Tuple[float | None, float | None]
    ) -> None:
        self.master.bounds[i] = bounds

    def copy(self, deep: bool = False) -> 'ColGenMILP':
        """
        Shallow copy (if `deep=False`) of self with
        bounds being a shallow copy of bounds
        and node choice method reinitialized
        """
        if deep:
            return cast(ColGenMILP, super().copy(deep=deep))
        child = cast(ColGenMILP, super().copy(deep=deep))
        child.milp = self.milp.copy()
        child.master = MILPMaster(child.milp)
        child.solution = child.milp.solution
        return child
