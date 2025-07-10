from typing import Optional

from bnbpy.cython.problem import Problem
from bnbpy.cython.solution import Solution

class Node:
    """Class for representing a node in a search tree."""
    problem: Problem
    parent: Optional['Node']
    level: int
    lb: float
    children: list[Node]
    _sort_index: int

    def __init__(
        self, problem: Problem, parent: Optional['Node'] = None
    ) -> None:
        """Instantiates a new `Node` object based on a (sub)problem.
        The node is evaluated in terms of lower bound as it is initialized.

        Parameters
        ----------
        problem : Problem
            Problem instance derived from parent node

        parent : Optional[Node], optional
            Parent node itself, if not root, by default None
        """
        ...

    def cleanup(self) -> None:
        ...

    def __lt__(self, other: 'Node') -> bool:
        ...

    @property
    def solution(self) -> Solution:
        ...

    @property
    def index(self) -> int:
        ...

    def compute_bound(self) -> None:
        """
        Computes the lower bound of the problem and sets it to
        problem attribute `lb`, which is referenced as a `Node` property.
        """
        ...

    def check_feasible(self) -> bool:
        """Calls `problem` `check_feasible()` method"""
        ...

    def set_solution(self, solution: Solution) -> None:
        """Calls method `set_solution` of problem, which also computes
        its lower bound if not yet solved.

        Parameters
        ----------
        solution : Solution
            New solution to overwrite current
        """
        ...

    def fathom(self) -> None:
        """Sets solution status of node as 'FATHOMED'"""
        ...

    def copy(self, deep: bool = True) -> 'Node':
        ...

    def deep_copy(self) -> 'Node':
        ...

    def branch(self) -> list['Node']:
        """Calls `problem` `branch()` method to create derived sub-problems.
        Each subproblem is used to instantiate a child node.
        Child nodes are evaluated in terms of lower bound as they are
        initialized.

        Returns
        -------
        Optional[List['Node']]
            List of child nodes, if any
        """
        ...

    def child_problem(self, problem: Problem) -> 'Node':
        ...

    def shallow_copy(self) -> 'Node':
        ...
