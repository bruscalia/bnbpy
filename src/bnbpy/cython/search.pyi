from typing import Any, Generic, Literal, Optional, TypeVar, Union

from bnbpy.cython.node import Node
from bnbpy.cython.priqueue import BasePriQueue
from bnbpy.cython.problem import Problem
from bnbpy.cython.solution import Solution
from bnbpy.cython.status import OptStatus
from bnbpy.logger import SearchLogger

P = TypeVar('P', bound=Problem)

class SearchResults(Generic[P]):
    """Results container for Branch & Bound search"""

    solution: Solution
    problem: P

    def __init__(self, solution: Solution, problem: P) -> None:
        """Initialize SearchResults

        Parameters
        ----------
        solution : Solution
            The best solution found

        problem : Problem
            The problem instance corresponding to the solution
        """
        ...

    def __repr__(self) -> str: ...

    def __str__(self) -> str: ...

    @property
    def cost(self) -> float:
        """Cost of the best solution found"""
        ...

    @property
    def lb(self) -> float:
        """Lower bound of the search"""
        ...

    @property
    def status(self) -> OptStatus:
        """Optimization status"""
        ...

class BranchAndBound:
    """Class for solving optimization problems via Branch & Bound"""

    problem: Problem
    root: Node
    gap: float
    queue: BasePriQueue
    rtol: float
    atol: float
    explored: int
    eval_node: str
    eval_in: bool
    eval_out: bool
    save_tree: bool
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
    def ub(self) -> float: ...

    @property
    def lb(self) -> float: ...

    @property
    def solution(self) -> Solution: ...

    def solve(
        self,
        problem: P,
        maxiter: Optional[int] = None,
        timelimit: Optional[Union[int, float]] = None
    ) -> SearchResults[P]:
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
        SearchResults
            Search results containing best solution and problem instance
        """
        ...

    def enqueue(self, node: Node) -> None:
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

    def branch(self, node: Node) -> None:
        """From a given node, create children nodes and enqueue them

        Parameters
        ----------
        node : Node
            Node being evaluated
        """
        ...

    def fathom(self, node: Node) -> None:  # noqa: PLR6301
        """Fathom node (by default is not deleted)

        If deletion is required for managing memory, remember to delete
        node from parent `children` attribute

        Parameters
        ----------
        node : Node
            Node to be fathomed
        """
        ...

    def pre_eval_callback(self, node: Node) -> None:
        """Abstraction for callbacks before node bound evaluation"""
        ...

    def post_eval_callback(self, node: Node) -> None:
        """Abstraction for callbacks after node bound evaluation"""
        ...

    def enqueue_callback(self, node: Node) -> None:
        """Abstraction for callbacks after node is enqueued"""
        ...

    def dequeue_callback(self, node: Node) -> None:
        """Abstraction for callbacks after node is dequeued"""
        ...

    def solution_callback(self, node: Node) -> None:
        """Abstraction for callback when a candidate
        feasible solution is verified (before being set)
        """
        ...

    def set_solution(self, node: Node) -> None:
        """Assigns the current node as incumbent, updates gap and calls
        `solution_callback`

        Parameters
        ----------
        node : Node
            New solution node
        """
        ...

    def log_row(self, message: Any) -> None:
        """Log a row to the search logger.

        Parameters
        ----------
        message : Any
            Message to log
        """
        ...

class BreadthFirstBnB(BranchAndBound):
    """Breadth-first Branch & Bound algorithm"""

    def __init__(
        self,
        rtol: float = 1e-4,
        atol: float = 1e-4,
        eval_node: Literal['in', 'out', 'both'] = 'out',
        save_tree: bool = False
    ) -> None:
        """Initialize Breadth-First Branch & Bound algorithm.

        Parameters
        ----------
        rtol : float, optional
            Relative tolerance for termination, by default 1e-4

        atol : float, optional
            Absolute tolerance for termination, by default 1e-4

        eval_node : Literal['in', 'out', 'both'], optional
            Node evaluation strategy, by default 'out'

        save_tree : bool, optional
            Whether to save node relationships, by default False
        """
        ...

class DepthFirstBnB(BranchAndBound):
    """Depth-first Branch & Bound algorithm"""
    # Just an alias - uses DFS queue by default
    ...

class BestFirstBnB(BranchAndBound):
    """Best-first Branch & Bound algorithm"""

    def __init__(
        self,
        rtol: float = 1e-4,
        atol: float = 1e-4,
        eval_node: Literal['in', 'out', 'both'] = 'out',
        save_tree: bool = False
    ) -> None:
        """Initialize Best-First Branch & Bound algorithm.

        Parameters
        ----------
        rtol : float, optional
            Relative tolerance for termination, by default 1e-4

        atol : float, optional
            Absolute tolerance for termination, by default 1e-4

        eval_node : Literal['in', 'out', 'both'], optional
            Node evaluation strategy, by default 'out'

        save_tree : bool, optional
            Whether to save node relationships, by default False
        """
        ...

def configure_logfile(
    filename: str, only_messages: bool = True, mode: str = 'a', **kwargs: Any
) -> None:
    """Configure logfile to write solution INFO messages

    Parameters
    ----------
    filename : str
        Nameof target file

    mode : str, optional
        FileHandler writing mode, by default 'a' (append)
    """
    ...
