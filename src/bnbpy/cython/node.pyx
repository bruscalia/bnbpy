# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

cimport cython
from libc.math cimport INFINITY
from libcpp cimport bool

import copy

from bnbpy.cython.counter cimport Counter
from bnbpy.cython.problem cimport Problem, P
from bnbpy.cython.solution cimport Solution


cdef:
    double LARGE_POS = INFINITY
    double LOW_NEG = -INFINITY


@cython.final
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

    cpdef void cleanup(self):
        cdef:
            Node child

        self.problem = None
        if self.children:
            for child in self.children:
                child.parent = None
            self.children = None
        self.parent = None

    def __lt__(self, Node other):
        return self._sort_index > other._sort_index

    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return id(self)

    @classmethod
    def __class_getitem__(cls, item: type[Problem]):
        """Support generic syntax Node[P] at runtime."""
        if not issubclass(item, Problem):
            raise TypeError(
                "Node can only be parameterized"
                f" with a Problem subclass, got {item}"
            )
        return cls

    @property
    def solution(self) -> Solution:
        return self.get_solution()

    @property
    def index(self):
        return self._sort_index

    cpdef void compute_bound(self):
        """Computes the lower bound of the problem and sets it to
        problem attribute `lb`, which is referenced as a `Node` property.
        """
        self.problem.compute_bound()
        self.lb = max(self.lb, self.problem.get_lb())

    cpdef bool check_feasible(self):
        """Calls `problem` `check_feasible()` method

        Returns
        -------
        bool
            Feasibility check result
        """
        return self.problem.check_feasible()

    cpdef void set_solution(self, Solution solution):
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

    cpdef list[Node] branch(self):
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

    cpdef Node primal_heuristic(self):
        """Calls `problem` `primal_heuristic()`
        method to generate a feasible
        solution from the current node, if any.

        Returns
        -------
        Node | None
            A child node with a feasible solution, if any
        """
        cdef:
            Problem prob_child
            Node child

        prob_child = self.problem.primal_heuristic()
        if prob_child is None:
            return None

        # The current node is not a parent
        # to avoid issues with counting and indexing of nodes
        child = init_node(prob_child, None)
        # Enforce the lower bound to -infinity as
        # if is not strictly worse than self
        # and should be formally computed next
        child.lb = LOW_NEG
        child.compute_bound()
        if not child.check_feasible():
            return None
        return child

    cdef void c_upgrade_bound(self):
        cdef:
            double new_lb
        new_lb = self.problem.stronger_bound()
        if new_lb > self.lb:
            self.problem.upgrade_bound(new_lb)
            self.lb = new_lb

    cpdef void upgrade_bound(self):
        """Calls `problem` `upgrade_bound()` method to compute a stronger
        lower bound, if possible, and updates node's lower bound accordingly.
        """
        self.c_upgrade_bound()

    cdef Node child_problem(self, P problem):
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

    cdef Node shallow_copy(self):
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


cdef Node init_node(P problem, Node parent=None):
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
