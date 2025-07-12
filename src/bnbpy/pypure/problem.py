import copy
from abc import ABC, abstractmethod
from typing import Generic, Optional, Sequence, TypeVar, Union

from bnbpy.pypure.solution import Solution
from bnbpy.pypure.status import OptStatus

S = TypeVar("S", bound=Solution)


class Problem(ABC, Generic[S]):
    """Abstraction for an optimization problem"""

    solution: S
    """Solution of the (sub)problem (if any)"""

    @abstractmethod
    def __init__(self) -> None:
        """Initialization method. Must set attribute `solution` here.
        """
        self.solution: S
        pass

    def __del__(self) -> None:
        self.cleanup()

    def cleanup(self) -> None:
        del self.solution

    @abstractmethod
    def calc_bound(self) -> Union[int, float]:
        """Returns a lower bound of the (sub)problem."""
        pass

    @abstractmethod
    def is_feasible(self) -> bool:
        """
        Returns `True` if the problem in its complete
        form has a feasible solution.
        """
        pass

    @abstractmethod
    def branch(self) -> Optional[Sequence['Problem'[S]]]:
        """Generates child nodes (problems) by branching."""
        pass

    @property
    def lb(self) -> Union[int, float]:
        """Lower bound of solution"""
        return self.solution.lb

    def compute_bound(self) -> None:
        """
        Computes the lower bound of the (sub)problem via `calc_bound`
        and sets it as the value of the attribute `lb`
        of the instance and solution.
        """
        lb = self.calc_bound()
        self.solution.set_lb(lb)

    def check_feasible(self) -> bool:
        """
        Verifies is the (sub)problem is feasible considering the
        complete formulation by calling `is_feasible` and uses the
        result to set the status of the solution.

        Returns
        -------
        bool
            Feasibility check
        """
        feas = self.is_feasible()
        if feas:
            self.solution.set_feasible()
        else:
            self.solution.set_infeasible()
        return feas

    def set_solution(self, solution: S) -> None:
        """Overwrites problem solution and computes lower bound in case
        if is not yet solved

        Parameters
        ----------
        solution : Solution
            New solution to overwrite current
        """
        self.solution = solution
        if self.solution.status == OptStatus.NO_SOLUTION:
            self.compute_bound()

    def warmstart(self) -> Optional[S]:  # noqa: PLR6301
        """This is a white label for warmstart
        If the problem has a warmstart function that returns a valid
        solution, it will be used at the begining of the search tree.

        Returns
        -------
        Optional[Solution]
            Solution to the problem, or None (in case not implemented)
        """
        return None

    def copy(self, deep: bool = True) -> 'Problem'[S]:
        if deep:
            return self.deep_copy()
        return self.shallow_copy()

    def deep_copy(self) -> 'Problem'[S]:
        other = copy.deepcopy(self)
        return other

    def shallow_copy(self) -> 'Problem'[S]:
        other = copy.copy(self)
        return other
