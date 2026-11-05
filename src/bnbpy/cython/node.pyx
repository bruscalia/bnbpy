# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

cimport cython
from libc.math cimport INFINITY
from libcpp cimport bool

import copy

from bnbpy.cython.counter cimport Counter
from bnbpy.cython.problem cimport Problem
from bnbpy.cython.solution cimport Solution


cdef:
    double LOW_NEG = -INFINITY


@cython.final
cdef class Node:
    """Class for representing a node in a search tree."""

    def __init__(
        self, Problem problem, Node parent=None
    ) -> None:
        """Instantiates a new `Node` object based on a (sub)problem.
        The node inherits the lower bound of its parent (or of the problem
        solution, if root); it is only evaluated by `compute_bound`.

        Parameters
        ----------
        problem : Problem
            Problem instance derived from parent node

        parent : Optional[Node], optional
            Parent node itself, if not root, by default None
        """

        self.problem = problem
        self.parent = parent
        self.children = None
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
        """Releases the problem and the links to the parent and children
        (called when the node is no longer needed in the search)."""
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
        """Computes the lower bound of the problem and updates the node
        attribute `lb` as the maximum between its current value and the
        problem lower bound.
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
        """Copies the node. A shallow copy shares the problem, parent
        and level with this node (with a new index); a deep copy
        copies the whole node."""
        if deep:
            return self.deep_copy()
        return self.shallow_copy()

    cpdef list[Node] branch(self):
        """Calls `problem` `branch()` method to create derived sub-problems.
        Each subproblem is used to instantiate a child node, which inherits
        the lower bound of this node (it is not evaluated here).

        Returns
        -------
        list[Node]
            List of child nodes, if any
        """
        cdef:
            int i
            Problem prob_child
            list[Problem] prob_children
            list[Node] children

        prob_children = self.problem.branch()
        if prob_children is None:
            return []

        children = [None] * len(prob_children)
        for i in range(len(prob_children)):
            prob_child = prob_children[i]
            children[i] = self.child_problem(prob_child)
        return children

    cpdef void save_children(self, list[Node] children):
        """Saves the list of child nodes to `children` attribute of the node.

        Parameters
        ----------
        children : list[Node]
            List of child nodes to save
        """
        self.children = children

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
        """Calls `problem` `stronger_bound()` and, if the result is greater
        than the current node lower bound, sets it via
        `problem.upgrade_bound()` and updates the node lower bound.
        """
        self.c_upgrade_bound()

    cdef Node child_problem(self, Problem problem):
        cdef:
            Node other
        other = Node.__new__(Node)
        other.problem = problem
        other.parent = self
        other.children = None
        other._counter = self._counter
        other.lb = self.lb
        other.level = self.level + 1
        other._sort_index = other._counter.next()
        return other

    cdef Node shallow_copy(self):
        cdef:
            Node other
        # Same problem, parent and level; only the sort index is new
        other = Node.__new__(Node)
        other.problem = self.problem
        other.parent = self.parent
        other.children = None
        other._counter = self._counter
        other.lb = self.lb
        other.level = self.level
        other._sort_index = other._counter.next()
        return other


cdef Node init_node(Problem problem, Node parent=None):
    cdef:
        Node node
    node = Node.__new__(Node)
    node.problem = problem
    node.parent = parent
    node.children = None
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
