from abc import abstractmethod
from typing import Optional, Sequence, Union

from bnbpy.cython.solution import Solution

class Problem:
    """
    Abstraction for an optimization problem

    IMPORTANT: Always remember to implement the methods:
        - `calc_bound`
        - `is_feasible`
        - `branch`

    Although not implemented using an abstract base class,
    due to Cython limitations, these methods are essential for the
    correct functioning of the branch-and-bound algorithm.

    Note that the Cython implementation uses static typing,
    so the `solution` attribute class must be a subclass of
    `bnbpy.cython.solution.Solution`.
    """

    solution: Solution
    """Solution of the (sub)problem (if any)"""

    def __init__(self) -> None:
        """
        Initializes the problem with an empty solution.
        """
        ...

    def __del__(self) -> None: ...

    @abstractmethod
    def calc_bound(self) -> Union[int, float]:
        """Returns a lower bound of the (sub)problem."""
        ...

    @abstractmethod
    def is_feasible(self) -> bool:
        """
        Returns `True` if the problem in its complete
        form has a feasible solution.
        """
        ...

    @abstractmethod
    def branch(self) -> Sequence['Problem']:
        """Generates child nodes (problems) by branching."""
        ...

    @property
    def lb(self) -> Union[int, float]:
        ...

    def compute_bound(self) -> None:
        """
        This method is not intented to be modified by the user.
        It is supposed to be called by the B&B algorithm with additional
        transparent calculations after compiting the bound via `calc_bound`.

        Computes the lower bound of the (sub)problem via `calc_bound`
        and sets it as the value of the attribute `lb`
        of the instance and solution.
        """
        ...

    def check_feasible(self) -> bool:
        """
        This method is not intented to be modified by the user.
        It is supposed to be called by the B&B algorithm with additional
        transparent calculations after checking the feasibility
        via `is_feasible`.

        Verifies is the (sub)problem is feasible considering the
        complete formulation by calling `is_feasible` and uses the
        result to set the status of the solution.

        Returns
        -------
        bool
            Feasibility check
        """
        ...

    def set_solution(self, solution: Solution) -> None:
        """
        This method is not intented to be modified by the user.
        It is supposed to be called by the B&B algorithm with additional
        transparent calculations when setting a new solution.

        Overwrites problem solution and computes lower bound in case
        if is not yet solved

        Parameters
        ----------
        solution : Solution
            New solution to overwrite current
        """
        ...

    def warmstart(self) -> Optional['Problem']:
        """This is a white label for warmstart
        If the problem has a warmstart function that returns a feasible
        problem state, it will be used at the begining of the search tree.

        Be careful not to modify the current problem instance,
        but return a new one.

        Returns
        -------
        Optional[Problem]
            Problem modified in a warmstart form, or None
            (in case not implemented)
        """
        ...

    def copy(self, deep: bool = True) -> 'Problem': ...
