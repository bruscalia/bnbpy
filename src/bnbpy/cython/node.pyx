# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool

import copy
import itertools
from typing import List, Optional, Union

from bnbpy.problem import Problem
from bnbpy.solution import Solution


cdef class Node:
    """Class for representing a node in a search tree."""

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

    def __del__(self):
        self.cleanup()

    cpdef void cleanup(self):
        if self.problem:
            del self.problem
            self.problem = None
        if self.children:
            for child in self.children:
                child.parent = None
        if self.parent:
            self.parent = None

    def __lt__(self, other: 'Node'):
        return self._sort_index > other._sort_index

    @property
    def solution(self) -> Solution:
        return self.problem.solution

    @property
    def index(self):
        return self._sort_index

    cpdef void compute_bound(Node self):
        """
        Computes the lower bound of the problem and sets it to
        problem attribute `lb`, which is referenced as a `Node` property.
        """
        self.problem.compute_bound()
        self.lb = max(self.lb, self.problem.lb)

    cpdef bool check_feasible(Node self):
        """Calls `problem` `check_feasible()` method"""
        return self.problem.check_feasible()

    cpdef void set_solution(Node self, solution: Solution):
        """Calls method `set_solution` of problem, which also computes
        its lower bound if not yet solved.

        Parameters
        ----------
        solution : Solution
            New solution to overwrite current
        """
        self.problem.set_solution(solution)
        self.lb = self.problem.lb

    cpdef void fathom(Node self):
        """Sets solution status of node as 'FATHOMED'"""
        self.solution.fathom()

    def copy(self, deep=True):
        if deep:
            return self.deep_copy()
        return self.shallow_copy()

    def deep_copy(self):
        other = copy.deepcopy(self)
        return other

    cpdef list[Node] branch(Node self):
        """Calls `problem` `branch()` method to create derived sub-problems.
        Each subproblem is used to instantiate a child node.
        Child nodes are evaluated in terms of lower bound as they are
        initialized.

        Returns
        -------
        Optional[List['Node']]
            List of child nodes, if any
        """
        cdef:
            list prob_children
            list[Node] children

        prob_children = self.problem.branch()
        if prob_children is None:
            return []
        children = [
            self.child_problem(prob_child)
            for prob_child in prob_children
        ]
        self.children = children
        return self.children

    cpdef Node child_problem(Node self, object problem):
        other = Node.__new__(Node)
        other.problem = problem
        other.parent = self
        other.children = []
        other._counter = self._counter
        other.lb = self.lb
        other.level = self.level + 1
        other._sort_index = next(other._counter)
        return other

    cpdef Node shallow_copy(Node self):
        other = Node.__new__(Node)
        other.problem = self.problem
        other.parent = self
        other.children = []
        other._counter = self._counter
        other.lb = self.lb
        other.level = self.level + 1
        other._sort_index = next(other._counter)
        return other
