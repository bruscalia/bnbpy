import copy
import itertools
from typing import List, Optional, Union

from bnbpy.problem import Problem
from bnbpy.solution import Solution


class Node:
    """Class for representing a node in a search tree."""

    problem: Problem
    parent: Optional['Node']
    level: int
    lb: Union[float, int]
    children: List['Node']
    _sort_index: int
    _counter = itertools.count

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
            self._counter = itertools.count()
            self.level = 0
            self.lb = self.problem.lb
        else:
            self._counter = self.parent._counter
            self.lb = self.parent.lb
            self.level = parent.level + 1
        self._sort_index = next(self._counter)

    def __lt__(self, other: 'Node'):
        return self._sort_index > other._sort_index

    @property
    def solution(self) -> Solution:
        return self.problem.solution

    @property
    def index(self):
        return self._sort_index

    def compute_bound(self, **options):
        """
        Computes the lower bound of the problem and sets it to
        problem attribute `lb`, which is referenced as a `Node` property.
        """
        self.problem.compute_bound(**options)
        self.lb = self.problem.lb

    def check_feasible(self):
        """Calls `problem` `check_feasible()` method"""
        return self.problem.check_feasible()

    def branch(self) -> Optional[List['Node']]:
        """Calls `problem` `branch()` method to create derived sub-problems.
        Each subproblem is used to instantiate a child node.
        Child nodes are evaluated in terms of lower bound as they are
        initialized.

        Returns
        -------
        Optional[List['Node']]
            List of child nodes, if any
        """
        prob_children = self.problem.branch()
        if prob_children is None:
            return None
        children = [
            Node(problem=prob_child, parent=self)
            for prob_child in prob_children
        ]
        self.children = children
        return self.children

    def set_solution(self, solution: Solution):
        """Calls method `set_solution` of problem, which also computes
        its lower bound if not yet solved.

        Parameters
        ----------
        solution : Solution
            New solution to overwrite current
        """
        self.problem.set_solution(solution)
        self.lb = self.problem.lb

    def fathom(self):
        """Sets solution status of node as 'FATHOMED'"""
        self.solution.fathom()

    def copy(self, deep=True):
        if deep:
            return self.deep_copy()
        return self.shallow_copy()

    def deep_copy(self):
        other = copy.deepcopy(self)
        return other

    def shallow_copy(self):
        other = copy.copy(self)
        return other
