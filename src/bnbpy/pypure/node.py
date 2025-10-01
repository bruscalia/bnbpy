import copy
from typing import List, Optional, Union

from bnbpy.pypure.counter import Counter
from bnbpy.pypure.problem import Problem
from bnbpy.pypure.solution import Solution


class Node:
    """Class for representing a node in a search tree."""

    problem: Problem
    parent: Optional['Node']
    level: int
    lb: Union[float, int]
    children: List['Node']
    _sort_index: int
    _counter: Counter

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
        self.problem = problem
        self.parent = parent
        self.children = []
        if parent is None:
            self._counter = Counter()
            self.level = 0
            self.lb = self.problem.get_lb()
        else:
            self._counter = parent._counter
            self.lb = parent.lb
            self.level = parent.level + 1
        self._sort_index = self._counter.next()

    def __del__(self) -> None:
        self.cleanup()

    def cleanup(self) -> None:
        if self.problem:
            self.problem = None  # type: ignore
        if self.children is not None:
            for child in self.children:
                child.parent = None
            self.children = None  # type: ignore
        if self.parent:
            self.parent = None

    def __lt__(self, other: 'Node') -> bool:
        return self._sort_index > other._sort_index

    @property
    def solution(self) -> Solution:
        return self.get_solution()

    def get_solution(self) -> Solution:
        """Get solution from problem."""
        return self.problem.solution

    @property
    def index(self) -> int:
        return self._sort_index

    def compute_bound(self) -> None:
        """
        Computes the lower bound of the problem and sets it to
        problem attribute `lb`, which is referenced as a `Node` property.
        """
        self.problem.compute_bound()
        self.lb = max(self.lb, self.problem.get_lb())

    def check_feasible(self) -> bool:
        """Calls `problem` `check_feasible()` method"""
        return self.problem.check_feasible()

    def branch(self) -> List['Node']:
        """Calls `problem` `branch()` method to create derived sub-problems.
        Each subproblem is used to instantiate a child node.
        Child nodes are evaluated in terms of lower bound as they are
        initialized.

        Returns
        -------
        List[Node]
            List of child nodes, if any
        """
        prob_children = self.problem.branch()
        if prob_children is None:
            return []
        children = [
            self.child_problem(prob_child)
            for prob_child in prob_children
        ]
        self.children = children
        return self.children

    def child_problem(self, problem: Problem) -> 'Node':
        """Create child node from problem - internal method matching Cython."""
        other = Node.__new__(Node)
        other.problem = problem
        other.parent = self
        other.children = []
        other._counter = self._counter
        other.lb = self.lb
        other.level = self.level + 1
        other._sort_index = other._counter.next()
        return other

    def set_solution(self, solution: Solution) -> None:
        """Calls method `set_solution` of problem, which also computes
        its lower bound if not yet solved.

        Parameters
        ----------
        solution : Solution
            New solution to overwrite current
        """
        self.problem.set_solution(solution)
        self.lb = self.problem.get_lb()

    def fathom(self) -> None:
        """Sets solution status of node as 'FATHOMED'"""
        self.solution.fathom()

    def copy(self, deep: bool = True) -> 'Node':
        if deep:
            return copy.deepcopy(self)
        return self.shallow_copy()

    def shallow_copy(self) -> 'Node':
        """Create shallow copy matching Cython implementation."""
        other = Node.__new__(Node)
        other.problem = self.problem
        other.parent = self
        other.children = []
        other._counter = self._counter
        other.lb = self.lb
        other.level = self.level + 1
        other._sort_index = other._counter.next()
        return other
