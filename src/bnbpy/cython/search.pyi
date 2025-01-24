from typing import Any, Literal, Optional, Union

from bnbpy.cython.node import Node
from bnbpy.logger import SearchLogger
from bnbpy.problem import Problem
from bnbpy.solution import Solution

class BranchAndBound:
    """Class for solving optimization problems via Branch & Bound"""

    problem: Problem
    root: Node
    gap: float
    queue: list[tuple[Any, Node]]
    rtol: float
    atol: float
    explored: int
    eval_in: bool
    eval_out: bool
    incumbent: Node
    bound_node: Node
    __logger: SearchLogger

    def __init__(
        self,
        rtol: float = 1e-4,
        atol: float = 1e-4,
        eval_node: Literal['in', 'out', 'both'] = 'out',
        save_tree: bool = False
    ) -> None:
        """Instantiate algoritm to solve problems via Branch & Bound.

        Note that the Cython implementation uses static typing,
        so the `Problem` class must be a subclass of
        `bnbpy.cython.problem.Problem`.

        Parameters
        ----------
        rtol : float, optional
            Relative tolerance for termination, by default 1e-4

        atol : float, optional
            Absolute tolerance for termination, by default 1e-4

        eval_node : Literal['in', 'out', 'both'], optional
            Node evaluation strategy, by default 'out' (as deque)

        save_tree : bool, optional
            Either or not to save node relationships, by default False.
            It can consume a lot of memory in large trees.
        """
        ...

    @property
    def ub(self) -> float:
        ...

    @property
    def lb(self) -> float:
        ...

    @property
    def solution(self) -> Solution:
        ...

    def solve(
        self,
        problem: Problem,
        maxiter: Optional[int] = None,
        timelimit: Optional[Union[int, float]] = None
    ) -> Optional[Solution]:
        """Solves optimization problem using Branch & Bound.

        Note that the Cython implementation uses static typing,
        so the `Problem` class must be a subclass of
        `bnbpy.cython.problem.Problem`.

        Parameters
        ----------
        problem : Problem
            Problem instance as in root node

        maxiter : Optional[int], optional
            Maximum number of iterations, by default None

        timelimit : Optional[Union[int, float]], optional
            Time limit in seconds, by default None

        Returns
        -------
        Optional[Solution]
            Best feasible solution found
        """
        ...

    def enqueue(self, node: Node):
        """Include new node into queue

        Parameters
        ----------
        node : Node
            Node to be included
        """
        ...

    def dequeue(self) -> Node:
        """Chooses the next evaluated node and computes its lower bound

        Returns
        -------
        Node
            Node to be evaluated
        """
        ...

    def branch(self, node: Node) -> Optional[list[Node]]:
        """From a given node, create children nodes and enqueue them

        Parameters
        ----------
        node : Node
            Node being evaluated
        """
        ...

    def fathom(self, node: Node):  # noqa: PLR6301
        """Fathom node (by default is not deleted)

        If deletion is required for managing memory, remember to delete
        node from parent `children` attribute

        Parameters
        ----------
        node : Node
            Node to be fathomed
        """
        ...

    def pre_eval_callback(self, node: Node):
        """Abstraction for callbacks before node bound evaluation"""
        ...

    def post_eval_callback(self, node: Node):
        """Abstraction for callbacks after node bound evaluation"""
        ...

    def enqueue_callback(self, node: Node):
        """Abstraction for callbacks after node is enqueued"""
        ...

    def dequeue_callback(self, node: Node):
        """Abstraction for callbacks after node is dequeued"""
        ...

    def solution_callback(self, node: Node):
        """
        Abstraction for callback when a candidate
        feasible solution is verified (before being set)
        """
        ...

    def set_solution(self, node: Node):
        """Assigns the current node as incumbent, updates gap and calls
        `solution_callback`

        Parameters
        ----------
        node : Node
            New solution node
        """
        ...

    def log_row(self, message: str):
        ...

class BreadthFirstBnB(BranchAndBound):
    """Breadth-first Branch & Bound algorithm"""

    def enqueue(self, node: Node):
        """Include new node into queue

        Parameters
        ----------
        node : Node
            Node to be included
        """
        ...

class DepthFirstBnB(BranchAndBound):
    """Depth-first Branch & Bound algorithm"""

    # Just an alias
    ...

class BestFirstBnB(BranchAndBound):
    """Relation priority Branch & Bound algorithm"""
    ...

def configure_logfile(
    filename: str, only_messages: bool = True, mode='a', **kwargs
):
    """Configure logfile to write solution INFO messages

    Parameters
    ----------
    filename : str
        Nameof target file

    mode : str, optional
        FileHandler writing mode, by default 'a' (append)
    """
    ...
