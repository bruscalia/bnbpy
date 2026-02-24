# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool

import copy

from bnbpy.cython.counter cimport Counter
from bnbpy.cython.problem cimport Problem
from bnbpy.cython.solution cimport Solution


cdef class Node:
    """Class for representing a node in a search tree."""

    def __init__(
        self, Problem problem, Node parent=None
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
            self._counter = self.parent._counter
            self.lb = self.parent.lb
            self.level = parent.level + 1
        self._sort_index = self._counter.next()

    cdef void cleanup(Node self):
        cdef:
            Node child

        if self.problem:
            self.problem = None
        if self.children is not None:
            for child in self.children:
                child.parent = None
            self.children = None
        if self.parent:
            self.parent = None

    def __lt__(self, other: 'Node'):
        return self._sort_index > other._sort_index

    @property
    def solution(self) -> Solution:
        return self.get_solution()

    @property
    def index(self):
        return self._sort_index

    cpdef void compute_bound(Node self):
        """Computes the lower bound of the problem and sets it to
        problem attribute `lb`, which is referenced as a `Node` property.
        """
        self.problem.compute_bound()
        self.lb = max(self.lb, self.problem.get_lb())

    cpdef bool check_feasible(Node self):
        """Calls `problem` `check_feasible()` method

        Returns
        -------
        bool
            Feasibility check result
        """
        return self.problem.check_feasible()

    cpdef void set_solution(Node self, Solution solution):
        """Calls method `set_solution` of problem, which also computes
        its lower bound if not yet solved.

        Parameters
        ----------
        solution : Solution
            New solution to overwrite current
        """
        self.problem.set_solution(solution)
        self.lb = self.problem.get_lb()

    cpdef Node copy(self, bool deep=True):
        if deep:
            return self.deep_copy()
        return self.shallow_copy()

    cpdef list[Node] branch(Node self):
        """Calls `problem` `branch()` method to create derived sub-problems.
        Each subproblem is used to instantiate a child node.
        Child nodes are evaluated in terms of lower bound as they are
        initialized.

        Returns
        -------
        list[Node]
            List of child nodes, if any
        """
        cdef:
            int i
            list prob_children
            list[Node] children

        prob_children = self.problem.branch()
        if prob_children is None:
            return []

        children = [None] * len(prob_children)
        for i in range(len(prob_children)):
            prob_child = prob_children[i]
            children[i] = self.child_problem(prob_child)
        self.children = children
        return children

    cdef Node child_problem(Node self, Problem problem):
        cdef:
            Node other
        other = Node.__new__(Node)
        other.problem = problem
        other.parent = self
        other.children = []
        other._counter = self._counter
        other.lb = self.lb
        other.level = self.level + 1
        other._sort_index = other._counter.next()
        return other

    cdef Node shallow_copy(Node self):
        cdef:
            Node other
        other = Node.__new__(Node)
        other.problem = self.problem
        other.parent = self
        other.children = []
        other._counter = self._counter
        other.lb = self.lb
        other.level = self.level + 1
        other._sort_index = other._counter.next()
        return other


cdef Node init_node(Problem problem, Node parent=None):
    cdef:
        Node node
    node = Node.__new__(Node)
    node.problem = problem
    node.parent = parent
    node.children = []
    if parent is None:
        node._counter = Counter()
        node.level = 0
        node.lb = node.problem.get_lb()
    else:
        node._counter = parent._counter
        node.lb = parent.lb
        node.level = parent.level + 1
    node._sort_index = node._counter.next()
    return node
