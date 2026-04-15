from typing import Any, Generic, Literal, Optional, TypeVar, Union

from bnbpy.cython.manager import BaseNodeManager
from bnbpy.cython.node import Node
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

class BranchAndBound(Generic[P]):
    """
    Class for solving optimization problems via Branch & Bound.

    This class adopts a DFS strategy by default,
    but can be easily customized by subclassing.

    Some alternative strategies are already implemented as subclasses:

    *   `DepthFirstBnB`: Depth-first (default) alias of `BranchAndBound`.
    *   `BreadthFirstBnB`: Breadth-first Branch & Bound algorithm.
    *   `BestFirstBnB`: Best-first Branch & Bound algorithm.
    *   `LifoBnB`: LIFO (last-in, first-out) strategy via `LifoManager`.
    *   `FifoBnB`: FIFO (first-in, first-out) strategy via `FifoManager`.

    Useful methods for subclassing and custom implementations:

    **Callback methods:**

    *   `pre_eval_callback`: Before node bound evaluation.
    *   `post_eval_callback`: After node bound evaluation.
    *   `enqueue_callback`: After node is enqueued.
    *   `dequeue_callback`: After node is dequeued.
    *   `solution_callback`: When a new feasible
        solution is obtained (after being set).

    **Core methods:**

    *   `enqueue`: Include new node into manager.
    *   `dequeue`: Chooses the next evaluated
        node and computes its lower bound.
    *   `branch`: From a given node, create children nodes and enqueue them.

    For a customization of enqueueing and dequeueing strategies,
    pass a custom ``manager`` (subclass of `BaseNodeManager`) at construction
    time, or override ``enqueue`` / ``dequeue`` in a subclass.
    """

    problem: P
    root: Node[P]
    gap: float
    manager: BaseNodeManager[P]
    rtol: float
    atol: float
    explored: int
    eval_node: str
    eval_in: bool
    eval_out: bool
    save_tree: bool
    incumbent: Node[P] | None
    bound_node: Node[P] | None
    __logger: SearchLogger

    def __init__(
        self,
        problem: P,
        eval_node: Literal['in', 'out', 'both'] = 'out',
        save_tree: bool = False,
        manager: BaseNodeManager[P] | None = None,
    ) -> None:
        """Instantiate algorithm to solve problems via Branch & Bound.

        Note that the Cython implementation uses static typing,
        so the `Problem` class must be a subclass of
        `bnbpy.cython.problem.Problem`.

        Parameters
        ----------
        problem : P
            Problem instance to solve

        eval_node : Literal['in', 'out', 'both'], optional
            Node[P] bound evaluation strategy, by default 'out'.

            *   'in': call `Problem.calc_bound` after
                parent `branch`, before inserting child nodes
                in the active manager. Useful when
                bound computation is inexpensive.

            *   'out': call `Problem.calc_bound` after
                selecting a node from the active manager.
                The result guides whether to explore
                (`is_feasible`, possibly `branch`) or
                prune. Often paired with fast enqueue
                proxies for node quality, such as MILP
                pseudo-costs.

            *   'both': evaluate in both moments above.

        save_tree : bool, optional
            Whether to save node relationships, by default False.
            It can consume a lot of memory in large trees.

        manager : BaseNodeManager, optional
            Node manager that controls the search traversal strategy.
            Defaults to ``DfsPriQueue()`` (depth-first search) when
            ``None`` is given.  Pass any ``BaseNodeManager`` subclass
            to customise the traversal order, or use the
            :meth:`build_manager` factory for common string aliases.
        """
        ...

    @staticmethod
    def build_manager(strategy: str) -> BaseNodeManager[Any]:
        """Factory method that returns a :class:`BaseNodeManager` for the
        given traversal strategy name.

        Parameters
        ----------
        strategy : str
            One of ``'dfs'``, ``'bfs'``, ``'best'``,
            ``'lifo'``, ``'fifo'``, ``'cbfs'``.

            *   ``'dfs'``  — Depth-first search (``DfsPriQueue``).
            *   ``'bfs'``  — Breadth-first search (``BfsPriQueue``).
            *   ``'best'`` — Best-first search (``BestPriQueue``).
            *   ``'lifo'`` — Last-in first-out stack (``LifoManager``).
            *   ``'fifo'`` — First-in first-out queue (``FifoManager``).
            *   ``'cbfs'`` — Cycle best-first search (``CycleQueue``).

        options : Any
            Additional keyword arguments to pass to the manager constructor.

        Returns
        -------
        BaseNodeManager
            The corresponding manager instance.

        Raises
        ------
        ValueError
            If *strategy* is not one of the recognised names.
        """
        ...

    def set_manager(self, manager: BaseNodeManager[P]) -> None:
        """Set a new node manager for the search.

        Parameters
        ----------
        manager : BaseNodeManager
            The new manager to use for node storage and retrieval.
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
        maxiter: Optional[int] = None,
        timelimit: Optional[Union[int, float]] = None,
        rtol: Optional[float] = None,
        atol: Optional[float] = None,
    ) -> SearchResults[P]:
        """Solves optimization problem using Branch & Bound.

        Note that the Cython implementation uses static typing,
        so the `Problem` class must be a subclass of
        `bnbpy.cython.problem.Problem`.

        Call ``reset()`` before ``solve()`` to restart from scratch;
        otherwise a second call to ``solve()`` resumes from the current
        queue state.

        Parameters
        ----------
        maxiter : Optional[int], optional
            Maximum number of additional iterations, by default None

        timelimit : Optional[Union[int, float]], optional
            Time limit in seconds, by default None

        rtol : Optional[float], optional
            Relative tolerance for termination. If provided, permanently
            updates ``self.rtol``, by default None

        atol : Optional[float], optional
            Absolute tolerance for termination. If provided, permanently
            updates ``self.atol``, by default None

        Returns
        -------
        SearchResults
            Search results containing best solution and problem instance
        """
        ...

    def reset(self) -> None:
        """Reset the search state for a fresh solve.

        Clears the queue, incumbent, bound node, and root so that the
        next call to ``solve()`` starts from scratch.
        """
        ...

    def branch(self, node: Node[P]) -> None:
        """From a given node, create children nodes and enqueue them

        Parameters
        ----------
        node : Node[P]
            Node[P] being evaluated
        """
        ...

    def primal_heuristic(self, node: Node[P]) -> None:
        """Calls `Problem` `primal_heuristic()` via node
        entity to generate a feasible
        solution from the current node, if any.

        NOTE: By default this is never called in the search tree.
        It is intended to be called from a custom callback.

        Parameters
        ----------
        node : Node[P]
            Node[P] being evaluated
        """
        ...

    def upgrade_bound(self, node: Node[P]) -> None:
        """Calls `Problem` `stronger_bound()` via node
        entity to generate a better lower bound from the current node,
        if any.

        NOTE: By default this is never called in the search tree.
        It is intended to be called from a custom callback.

        Parameters
        ----------
        node : Node[P]
            Node[P] being evaluated
        """
        ...

    def fathom(self, node: Node[P]) -> None:  # noqa: PLR6301
        """Fathom node (by default is not deleted)

        If deletion is required for managing memory, remember to delete
        node from parent `children` attribute

        Parameters
        ----------
        node : Node[P]
            Node[P] to be fathomed
        """
        ...

    def pre_eval_callback(self, node: Node[P]) -> None:
        """Abstraction for callbacks before node bound evaluation"""
        ...

    def post_eval_callback(self, node: Node[P]) -> None:
        """Abstraction for callbacks after node bound evaluation"""
        ...

    def enqueue_callback(self, node: Node[P]) -> None:
        """
        Abstraction for callbacks immediately
        before node is enqueued, already after being evaluated.

        Parameters
        ----------
        node : Node
            Node that is about to be enqueued.
        """
        ...

    def dequeue_callback(self, node: Node[P]) -> None:
        """
        Abstraction for callbacks immediately
        after node is dequeued and possibly evaluated.

        Parameters
        ----------
        node : Node
            Node that was dequeued and evaluated (if `eval_out` is True).
        """
        ...

    def solution_callback(self, node: Node[P]) -> None:
        """Abstraction for callback when a candidate
        feasible solution is verified (before being set)
        """
        ...

    def set_solution(self, node: Node[P]) -> None:
        """Assigns the current node as incumbent, updates gap and calls
        `solution_callback`

        Parameters
        ----------
        node : Node[P]
            New solution node
        """
        ...

    def set_bound(self, node: Node[P]) -> None:
        """Public interface to set a new node as the
        new `bound_node`, which is a readonly attribute.

        Parameters
        ----------
        node : Node
            New bound node
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

class DepthFirstBnB(BranchAndBound[P]):
    """Depth-first Branch & Bound algorithm.

    Uses :class:`~bnbpy.cython.priqueue.DfsPriQueue` as the node manager.
    """

    ...

class BreadthFirstBnB(BranchAndBound[P]):
    """Breadth-first Branch & Bound algorithm.

    Uses :class:`~bnbpy.cython.priqueue.BfsPriQueue` as the node manager.
    """

    def __init__(
        self,
        problem: P,
        eval_node: Literal['in', 'out', 'both'] = 'out',
        save_tree: bool = False,
    ) -> None: ...

class BestFirstBnB(BranchAndBound[P]):
    """Best-first Branch & Bound algorithm.

    Uses :class:`~bnbpy.cython.priqueue.BestPriQueue` as the node manager.
    """

    def __init__(
        self,
        problem: P,
        eval_node: Literal['in', 'out', 'both'] = 'out',
        save_tree: bool = False,
    ) -> None: ...

class LifoBnB(BranchAndBound[P]):
    """Branch & Bound with a last-in first-out (LIFO) node manager.

    Uses :class:`~bnbpy.cython.manager.LifoManager` as the node manager.
    Equivalent to a pure stack-based DFS without bound-based tie-breaking.
    """

    def __init__(
        self,
        problem: P,
        eval_node: Literal['in', 'out', 'both'] = 'out',
        save_tree: bool = False,
    ) -> None: ...

class FifoBnB(BranchAndBound[P]):
    """Branch & Bound with a first-in first-out (FIFO) node manager.

    Uses :class:`~bnbpy.cython.manager.FifoManager` as the node manager.
    Equivalent to a pure queue-based BFS without bound-based tie-breaking.
    """

    def __init__(
        self,
        problem: P,
        eval_node: Literal['in', 'out', 'both'] = 'out',
        save_tree: bool = False,
    ) -> None: ...

def configure_logfile(
    filename: str, only_messages: bool = True, mode: str = 'a', **kwargs: Any
) -> None:
    """Configure logfile to write solution INFO messages

    Parameters
    ----------
    filename : str
        Name of target file

    mode : str, optional
        FileHandler writing mode, by default 'a' (append)
    """
    ...
