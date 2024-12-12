import copy
import math
from typing import Callable, List, Optional, Tuple, Union

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import OptimizeResult, linprog

from bnbprob.milpy.utils import BoundType
from bnbpy import Problem, Solution


class MILPSol(Solution):
    problem: 'MILP'
    scipy_res: Optional[OptimizeResult]
    x: Optional[np.ndarray]
    valid: Optional[bool]
    residuals: Optional[np.ndarray]

    def __init__(self, problem: 'MILP'):
        super().__init__()
        self.problem = problem
        self.scipy_res = None
        self.x: NDArray = None
        self.valid = None
        self.residuals = None

    def set_results(self, res: OptimizeResult):
        self.scipy_res = res
        self.x = res.x
        self.valid = res.success
        if self.valid:
            x_round = np.round(self.x, 0)
            self.residuals = abs(self.x - x_round) * self.problem.integrality

    def calc_bound(self):
        res = linprog(
            self.problem.c,
            A_ub=self.problem.A_ub,
            b_ub=self.problem.b_ub,
            A_eq=self.problem.A_eq,
            b_eq=self.problem.b_eq,
            bounds=self.problem.bounds,
        )
        self.set_results(res)
        lb = float('inf')
        if self.valid:
            lb = self.scipy_res.fun
        return lb


class MILP(Problem):
    """Mixed-Integer Linear Problem (compatible with scipy and bnbpy)"""
    solution: MILPSol
    c: NDArray
    A_ub: Optional[NDArray]
    b_ub: Optional[NDArray]
    A_eq: Optional[NDArray]
    b_eq: Optional[NDArray]
    bounds: Optional[Union[BoundType, List[BoundType]]]
    integrality: Union[NDArray, int, bool]
    tol: float
    residuals: Optional[NDArray]
    branching: str
    _rng: np.random.Generator
    _branching_rule: Callable

    def __init__(  # noqa: PLR0913, PLR0917
        self,
        c: NDArray,
        A_ub: Optional[NDArray] = None,
        b_ub: Optional[NDArray] = None,
        A_eq: Optional[NDArray] = None,
        b_eq: Optional[NDArray] = None,
        bounds: Optional[Union[BoundType, List[BoundType]]] = None,
        integrality: Optional[Union[NDArray, int]] = None,
        tol: float = 1e-4,
        branching: str = 'max',
        seed: Optional[int] = None,
    ):
        """Instantiate MILP (see `scipy.optimize.linprog` for argument details)

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

        tol : float, optional
            Integrality tolerance, by default 1e-4

        branching : str, optional
            Branching priority scheme, by default 'max'

        seed : Optional[int], optional
            Random seed in case of randomized branching, by default None
        """
        super().__init__()
        # If integrality is None, variables are assumed integer
        if integrality is None or integrality is True:
            integrality = 1.0
        elif integrality is False:
            integrality = 0.0

        # Init parameters based on scipy
        self.c = c
        self.A_ub = A_ub
        self.b_ub = b_ub
        self.A_eq = A_eq
        self.b_eq = b_eq
        self._init_bounds(bounds)  # convert into array
        self.integrality = integrality
        self.tol = tol
        self.branching = branching
        self._rng = np.random.default_rng(seed)
        self._init_branching()
        self.solution = MILPSol(self)

    def _init_branching(self):
        if self.branching == 'min':
            self._branching_rule = self._minimum_violation
        elif self.branching == 'max':
            self._branching_rule = self._maximum_violation
        elif self.branching == 'random':
            self._branching_rule = self._random_violation
        elif self.branching == 'mixed':
            self._branching_rule = self._mixed_violation
        else:
            raise ValueError(f'Unrecognized branching rule {self.branching}')

    def _init_bounds(
        self, bounds: Optional[Union[BoundType, List[BoundType]]]
    ):
        if bounds is None:
            bounds = [(0, None) for _ in range(len(self.c))]
        elif isinstance(bounds, tuple):
            bounds = [(*bounds,) for _ in range(len(self.c))]
        self.bounds = bounds

    def set_solution(self, solution: MILPSol):
        super().set_solution(solution)
        solution.problem = self

    def calc_bound(self):
        return self.solution.calc_bound()

    @property
    def residuals(self):
        return self.solution.residuals

    def is_feasible(self):
        valid = np.all(self.residuals <= self.tol)
        if valid:
            self.solution.cost = self.solution.lb
        return valid

    def update_bounds(self, i: int, bounds: Tuple[int, int]):
        self.bounds[i] = bounds

    def branch(self) -> Optional[List['MILP']]:
        # If not successful, just return
        if not self.solution.valid:
            self.solution.set_infeasible()
            return None

        # Choose branch var to define new limits
        i = self.choose_branch_var()
        xi_lb = math.ceil(self.solution.x[i])
        xi_ub = math.floor(self.solution.x[i])

        # Instantiate and return the two child nodes
        p1 = self.copy()
        p1.update_bounds(i, (xi_lb, self.bounds[i][-1]))
        p2 = self.copy()
        p2.update_bounds(i, (self.bounds[i][0], xi_ub))
        return [p1, p2]

    def choose_branch_var(self):
        i = self._branching_rule()
        return i

    def _minimum_violation(self):
        mask = self.residuals > self.tol
        var_indexes = np.arange(self.residuals.shape[0])
        j = np.argmin(self.residuals[mask])
        i = var_indexes[mask][j]
        return i

    def _maximum_violation(self):
        var_indexes = np.arange(self.residuals.shape[0])
        j = np.argmax(self.residuals)
        i = var_indexes[j]
        return i

    def _random_violation(self):
        mask = self.residuals > self.tol
        var_indexes = np.arange(self.residuals.shape[0])
        i = self._rng.choice(var_indexes[mask])
        return i

    def _mixed_violation(self):
        m = self._rng.choice([
            self._minimum_violation,
            self._maximum_violation,
            self._random_violation,
        ])
        return m()

    def copy(self, deep=False):
        """
        Shallow copy (if `deep=False`) of self with
        bounds being a shallow copy of bounds
        and node choice method reinitialized
        """
        if deep:
            return super().copy(deep=deep)
        child = super().copy(deep=deep)
        child.bounds = copy.copy(self.bounds)
        child._init_branching()
        child.solution = MILPSol(child)
        return child
