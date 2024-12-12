import logging
import math
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

import numpy as np
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

    a_ub: Optional[np.ndarray] = None
    """Column coefficients (1d array)"""
    a_eq: Optional[np.ndarray] = None
    """Column coefficients (1d array)"""
    c: Union[int, float] = 0.0
    """Column partial cost in obj function (minimize)"""
    bounds: BoundType = (0, None)
    """Column bounds (tuple - scipy compatible)"""

    def __hash__(self):
        return hash(str(self))


@dataclass
class MILPDuals:
    """Dual information of MILP problem solution"""

    lower: Optional[np.ndarray] = None
    """Duals of lower bounds"""
    upper: Optional[np.ndarray] = None
    """Duals of upper bounds"""
    eqlin: Optional[np.ndarray] = None
    """Duals of equality constraints"""
    ineqlin: Optional[np.ndarray] = None
    """Duals of inequality constraints"""

    def __hash__(self):
        return hash(str(self))


class MILPMaster(Master):
    """Master Problem (MILP)"""

    milp: MILP
    """MILP instance that defines master problem"""

    def __init__(self, milp: MILP):
        self.milp = milp

    @property
    def c(self):
        return self.milp.c

    @c.setter
    def c(self, c: np.ndarray):
        self.milp.c = c

    @property
    def A_ub(self):
        return self.milp.A_ub

    @A_ub.setter
    def A_ub(self, A_ub: np.ndarray):
        self.milp.A_ub = A_ub

    @property
    def A_eq(self):
        return self.milp.A_eq

    @A_eq.setter
    def A_eq(self, A_eq: np.ndarray):
        self.milp.A_eq = A_eq

    @property
    def b_ub(self):
        return self.milp.b_ub

    @b_ub.setter
    def b_ub(self, b_ub: np.ndarray):
        self.milp.b_ub = b_ub

    @property
    def b_eq(self):
        return self.milp.b_eq

    @b_eq.setter
    def b_eq(self, b_eq: np.ndarray):
        self.milp.b_eq = b_eq

    @property
    def bounds(self):
        return self.milp.bounds

    @bounds.setter
    def bounds(self, bounds: np.ndarray):
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
                self.A_ub = np.hstack((self.A_ub, a_ub))
                valid = True
        if c.a_eq is not None:
            a_eq = c.a_eq.reshape(-1, 1)
            if not self._column_exists_eq(a_eq):
                self.A_eq = np.hstack((self.A_eq, a_eq))
                valid = True
        if valid:
            self.c = np.append(self.c, c.c)
            self.bounds.append(c.bounds)
        return valid

    def _column_exists_ub(self, a: np.ndarray):
        matches = self.A_ub == a
        return np.any(np.all(matches, axis=0))

    def _column_exists_eq(self, a: np.ndarray):
        matches = self.A_eq == a
        return np.any(np.all(matches, axis=0))

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
            lower=sol.lower.marginals,
            upper=sol.upper.marginals,
            eqlin=sol.eqlin.marginals,
            ineqlin=sol.ineqlin.marginals
        )
        return MasterSol(sol.fun, duals)

    def solve_ineq_dual(self) -> OptimizeResult:
        """Backup for dual solution stabilization alternative

        Returns
        -------
        OptimizeResult
            Scipy results for a dual formulation of the set cover problem
        """
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
        assert isinstance(
            pricing, Pricing
        ), 'Pricing must be valid instance of child class from `Pricing`'
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

    def set_solution(self, solution: Solution):
        self.milp.set_solution(solution)
        self.solution = self.milp.solution

    def is_feasible(self):
        return self.milp.is_feasible()

    def branch(self) -> Optional[List['MILP']]:
        # If not successful, just return
        if not self.solution.valid:
            self.solution.set_infeasible()
            return None

        # Choose branch var to define new limits
        i = self.milp.choose_branch_var()
        xi_lb = math.ceil(self.solution.x[i])
        xi_ub = math.floor(self.solution.x[i])

        # Instantiate and return the two child nodes
        p1 = self.copy()
        p1.update_bounds(i, (xi_lb, self.milp.bounds[i][-1]))
        p2 = self.copy()
        p2.update_bounds(i, (self.milp.bounds[i][0], xi_ub))
        return [p1, p2]

    def calc_bound(self):
        sol_master = self._calc_bound()
        lb = float('inf')
        if self.solution.valid:
            lb = math.ceil(round(sol_master.cost, 4))
        log.debug(f'Price finished: {lb:.2f}')
        return lb

    def update_bounds(self, i: int, bounds: Tuple[int, int]):
        self.master.bounds[i] = bounds

    def copy(self, deep=False):
        """
        Shallow copy (if `deep=False`) of self with
        bounds being a shallow copy of bounds
        and node choice method reinitialized
        """
        if deep:
            return super().copy(deep=deep)
        child = super().copy(deep=deep)
        child.milp = self.milp.copy()
        child.master = MILPMaster(child.milp)
        child.solution = child.milp.solution
        return child
