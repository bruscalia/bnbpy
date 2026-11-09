from typing import Generic, Optional, TypeVar

from bnbpy.cython.problem import Problem
from bnbpy.cython.solution import Solution

P = TypeVar('P', bound=Problem)

class Node(Generic[P]):
    """Class for representing a node in a search tree."""

    problem: P
    parent: Optional['Node[P]']
    level: int
    lb: float
    children: Optional[list['Node[P]']]
    _sort_index: int

    def __init__(self, problem: P, parent: 'Optional[Node[P]]' = None) -> None:
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
        ...

    def __lt__(self, other: 'Node[P]') -> bool: ...
    @property
    def solution(self) -> Solution: ...
    @property
    def index(self) -> int: ...
    def cleanup(self) -> None:
        """Releases the problem and the links to the parent and children
        (called when the node is no longer needed in the search)."""
        ...

    def compute_bound(self) -> None:
        """Computes the lower bound of the problem and updates the node
        attribute `lb` as the maximum between its current value and the
        problem lower bound.
        """
        ...

    def check_feasible(self) -> bool:
        """Calls `problem` `check_feasible()` method

        Returns
        -------
        bool
            Feasibility check result
        """
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

    def copy(self, deep: bool = True) -> 'Node[P]':
        """Copies the node. A shallow copy shares the problem, parent
        and level with this node (with a new index); a deep copy
        copies the whole node."""
        ...

    def branch(self) -> list['Node[P]']:
        """Calls `problem` `branch()` method to create derived sub-problems.
        Each subproblem is used to instantiate a child node, which inherits
        the lower bound of this node (it is not evaluated here).

        Returns
        -------
        list[Node]
            List of child nodes, if any
        """
        ...

    def save_children(self, children: list['Node[P]']) -> None:
        """Saves the list of child nodes to the
        `children` attribute of the node.

        Parameters
        ----------
        children : list[Node]
            List of child nodes to be saved
        """
        ...

    def primal_heuristic(self) -> 'Node[P] | None':
        """Calls `problem` `primal_heuristic()`
        method to generate a feasible
        solution from the current node, if any.

        Returns
        -------
        Node[P] | None
            A child node with a feasible solution, if any
        """
        ...

    def upgrade_bound(self) -> None:
        """Calls `problem` `stronger_bound()` and, if the result is greater
        than the current node lower bound, sets it via
        `problem.upgrade_bound()` and updates the node lower bound.
        """
        ...
