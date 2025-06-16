import copy
import math
from typing import Callable, List, Optional, Sequence, Tuple, Union, cast

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
        self.x = None
        self.valid = None
        self.residuals = None

    def set_results(self, res: OptimizeResult) -> None:
        self.scipy_res = res
        self.x = cast(NDArray[np.float64], res.x)
        self.valid = res.success
        if self.valid:
            x_round = np.round(self.x, 0)
            self.residuals = abs(self.x - x_round) * self.problem.integrality

    def calc_bound(self) -> float:
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
            lb = cast(float, self.scipy_res.fun)  # type: ignore
        return lb


class MILP(Problem):
    """Mixed-Integer Linear Problem (compatible with scipy and bnbpy)"""

    solution: MILPSol
    c: NDArray[np.float64]
    A_ub: Optional[NDArray[np.float64]]
    b_ub: Optional[NDArray[np.float64]]
    A_eq: Optional[NDArray[np.float64]]
    b_eq: Optional[NDArray[np.float64]]
    bounds: List[BoundType]
    integrality: Union[NDArray[np.float64], int, bool, float]
    tol: float
    branching: str
    _rng: np.random.Generator
    _branching_rule: Callable[[], int]

    def __init__(  # noqa: PLR0913, PLR0917
        self,
        c: NDArray[np.float64],
        A_ub: Optional[NDArray[np.float64]] = None,
        b_ub: Optional[NDArray[np.float64]] = None,
        A_eq: Optional[NDArray[np.float64]] = None,
        b_eq: Optional[NDArray[np.float64]] = None,
        bounds: Optional[Union[BoundType, Sequence[BoundType]]] = None,
        integrality: Optional[Union[NDArray[np.float64], int, float]] = None,
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

    def _init_branching(self) -> None:
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
        self, bounds: Optional[Union[BoundType, Sequence[BoundType]]]
    ) -> None:
        if bounds is None:
            bounds = [(0, None) for _ in range(len(self.c))]
        elif isinstance(bounds, tuple):
            bounds = [(*bounds,) for _ in range(len(self.c))]
        self.bounds = cast(list[BoundType], bounds)

    def set_solution(self, solution: Solution) -> None:
        super().set_solution(solution)
        if isinstance(solution, MILPSol):
            solution.problem = self
        else:
            raise TypeError(
                'Solution must be an instance of MILPSol or its subclass'
            )

    def calc_bound(self) -> float:
        return self.solution.calc_bound()

    @property
    def residuals(self) -> NDArray[np.float64]:
        return cast(NDArray[np.float64], self.solution.residuals)

    def is_feasible(self) -> bool:
        valid = np.all(self.residuals <= self.tol)
        if valid:
            self.solution.cost = self.solution.lb
        return cast(bool, valid)

    def update_bounds(
        self, i: int, bounds: Tuple[float | None, float | None]
    ) -> None:
        self.bounds[i] = bounds

    def branch(self) -> Optional[Sequence['MILP']]:
        # If not successful, just return
        if not self.solution.valid:
            self.solution.set_infeasible()
            return None

        # Choose branch var to define new limits
        i = self.choose_branch_var()
        if self.solution.x is None:
            raise ValueError('Solution x is None, cannot branch')
        x_sol = cast(NDArray[np.float64], self.solution.x)
        xi_lb: float = math.ceil(x_sol[i])
        xi_ub: float = math.floor(x_sol[i])

        # Instantiate and return the two child nodes
        p1 = self.copy()
        p1.update_bounds(i, (xi_lb, self.bounds[i][-1]))
        p2 = self.copy()
        p2.update_bounds(i, (self.bounds[i][0], xi_ub))
        return [p1, p2]

    def choose_branch_var(self) -> int:
        i = self._branching_rule()
        return i

    def _minimum_violation(self) -> int:
        mask = self.residuals > self.tol
        var_indexes = np.arange(self.residuals.shape[0])
        j = np.argmin(self.residuals[mask])
        i: int = var_indexes[mask][j]
        return i

    def _maximum_violation(self) -> int:
        var_indexes = np.arange(self.residuals.shape[0])
        j = np.argmax(self.residuals)
        i: int = var_indexes[j]
        return i

    def _random_violation(self) -> int:
        mask = self.residuals > self.tol
        var_indexes = np.arange(cast(int, self.residuals.shape[0]))
        i: int = self._rng.choice(var_indexes[mask])
        return i

    def _mixed_violation(self) -> int:
        m = self._rng.choice([  # type: ignore
            self._minimum_violation,
            self._maximum_violation,
            self._random_violation,
        ])
        return cast(int, m())

    def copy(self, deep: bool = False) -> 'MILP':
        """
        Shallow copy (if `deep=False`) of self with
        bounds being a shallow copy of bounds
        and node choice method reinitialized
        """
        if deep:
            return cast(MILP, super().copy(deep=deep))
        child = cast(MILP, super().copy(deep=deep))
        child.bounds = copy.copy(self.bounds)
        child._init_branching()
        child.solution = MILPSol(child)
        return child
