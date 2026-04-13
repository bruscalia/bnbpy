# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libc.math cimport INFINITY
from libcpp cimport bool
from libcpp.string cimport string

import logging
import time
from typing import Any, List, Literal, Optional, Tuple, Union

from bnbpy.cython.manager cimport BaseNodeManager, FifoManager, LifoManager
from bnbpy.cython.node cimport Node, init_node
from bnbpy.cython.priqueue cimport (
    BestPriQueue,
    BfsPriQueue,
    DfsPriQueue,
)
from bnbpy.cython.problem cimport Problem
from bnbpy.cython.solution cimport Solution
from bnbpy.cython.status cimport OptStatus
from bnbpy.logger import SearchLogger

log = logging.getLogger(__name__)


cdef:
    double LARGE_POS = INFINITY
    double LOW_NEG = -INFINITY


cdef class SearchResults:
    """Results container for Branch & Bound search"""

    @classmethod
    def __class_getitem__(cls, item: type[Problem]):
        """Support generic syntax SearchResults[P] at runtime."""
        if not issubclass(item, Problem):
            raise TypeError(
                "SearchResults can only be parameterized"
                f" with a Problem subclass, got {item}"
            )
        return cls

    def __init__(
        self,
        Solution solution,
        Problem problem
    ) -> None:
        """Initialize SearchResults

        Parameters
        ----------
        solution : Solution
            The best solution found

        problem : Problem
            The problem instance corresponding to the solution
        """
        self.solution = solution
        self.problem = problem

    def __repr__(self) -> str:
        return str(self.solution)

    def __str__(self) -> str:
        return str(self.solution)

    @property
    def cost(self) -> float:
        """Cost of the best solution found"""
        return self.solution.cost

    @property
    def lb(self) -> float:
        """Lower bound of the search"""
        return self.solution.lb

    @property
    def status(self) -> OptStatus:
        """Optimization status"""
        return self.solution.status


cdef class BranchAndBound:
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

    def __init__(
        self,
        Problem problem,
        eval_node = 'out',
        save_tree: bool = False,
        manager: BaseNodeManager = None,
    ) -> None:
        """Instantiate algorithm to solve problems via Branch & Bound.

        Note that the Cython implementation uses static typing,
        so the `Problem` class must be a subclass of
        `bnbpy.cython.problem.Problem`.

        Parameters
        ----------
        problem : Problem
            Problem instance to solve

        eval_node : Literal['in', 'out', 'both'], optional
            Node bound evaluation strategy, by default 'out'.

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
        # Basic attribute initialization
        self.problem = problem

        # The root will be initialized at the first call to solve()
        # to allow warmstart, with a `None` check
        self.root = None
        self.explored = 0
        self.manager = manager if manager is not None else DfsPriQueue()

        # Default tolerances, might be overridden by solve() parameters
        self.rtol = 1e-4
        self.atol = 1e-4

        # Evaluation strategy flags
        self.eval_node = <string> eval_node.encode("utf-8")
        self.eval_in = self.eval_node in {'in', 'both'}
        self.eval_out = self.eval_node in {'out', 'both'}
        self.save_tree = save_tree

        # Core search attributes
        self.incumbent = None
        self.bound_node = None
        self.gap = INFINITY

        # Initialize logger
        self.__logger = SearchLogger(log)

    @classmethod
    def __class_getitem__(cls, item: type[Problem]):
        """Support generic syntax BranchAndBound[P] at runtime."""
        if not issubclass(item, Problem):
            raise TypeError(
                "BranchAndBound can only be parameterized"
                f" with a Problem subclass, got {item}"
            )
        return cls

    @property
    def ub(self):
        return self.get_ub()

    cdef double get_ub(BranchAndBound self):
        if self.incumbent is not None:
            return self.incumbent.lb
        return LARGE_POS

    @property
    def lb(self):
        return self.get_lb()

    cdef double get_lb(BranchAndBound self):
        if self.bound_node is not None:
            return min(self.bound_node.lb, self.get_ub())
        return LOW_NEG

    @property
    def solution(self):
        return self.get_solution()

    cdef Solution get_solution(BranchAndBound self):
        if self.incumbent is not None:
            return self.incumbent.get_solution()
        elif self.bound_node is not None:
            return self.bound_node.get_solution()
        return Solution()

    @staticmethod
    def build_manager(strategy: str) -> BaseNodeManager:
        """Factory method that returns a :class:`BaseNodeManager` for the
        given traversal strategy name.

        Parameters
        ----------
        strategy : str
            One of ``'dfs'``, ``'bfs'``, ``'best'``, ``'lifo'``, ``'fifo'``.

            *   ``'dfs'``  — Depth-first search (``DfsPriQueue``).
            *   ``'bfs'``  — Breadth-first search (``BfsPriQueue``).
            *   ``'best'`` — Best-first search (``BestPriQueue``).
            *   ``'lifo'`` — Last-in first-out stack (``LifoManager``).
            *   ``'fifo'`` — First-in first-out queue (``FifoManager``).

        Returns
        -------
        BaseNodeManager
            The corresponding manager instance.

        Raises
        ------
        ValueError
            If *strategy* is not one of the recognised names.
        """
        _strategies = {
            'dfs': DfsPriQueue,
            'bfs': BfsPriQueue,
            'best': BestPriQueue,
            'lifo': LifoManager,
            'fifo': FifoManager,
        }
        key = strategy.lower()
        if key not in _strategies:
            raise ValueError(
                f"Unknown strategy {strategy!r}. "
                f"Choose from: {list(_strategies)}"
            )
        return _strategies[key]()

    cdef void _restart_search(BranchAndBound self):
        self.incumbent = None
        self.bound_node = None
        self.gap = INFINITY
        self.manager.clear()

    def solve(
        self,
        maxiter: Optional[int] = None,
        timelimit: Optional[Union[int, float]] = None,
        rtol: Optional[float] = None,
        atol: Optional[float] = None,
    ) -> SearchResults:
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

        cdef:
            double start_time, current_time
            double _tlim = LARGE_POS
            unsigned long long _mxiter
            Node node
            Solution sol
            Problem inc_problem

        # Permanently update tolerances if provided
        if rtol is not None:
            self.rtol = rtol
        if atol is not None:
            self.atol = atol

        if timelimit is not None:
            _tlim = timelimit
        start_time = time.perf_counter()

        # Initialize on first call only
        if self.root is None:
            self._restart_search()
            log.info('Starting exploration of search tree')
            self._log_headers()
            self._warmstart(self.problem.warmstart())
            self._enqueue_root()

        # Additional iterations from current explored count
        if maxiter is not None:
            _mxiter = self.explored + <unsigned long long> maxiter
        else:
            _mxiter = ULLONG_MAX

        # In case the root node is already the LB of an optimal warmstart
        self._check_termination(_mxiter)
        while self.manager.not_empty():
            # Check for time termination
            if timelimit is not None:
                current_time = time.perf_counter()
                if current_time - start_time >= _tlim:
                    self.log_row('Time Limit')
                    break
            node = self._dequeue_core()
            # Avoid node with poor parents in case ub was updated meanwhile
            if node is not None:
                # Perform iteration (feasibility, bound check, and branching)
                self._do_iter(node)
            # Update LB if node is the one
            if node is self.bound_node:
                self._update_bound()
            # Termination by optimality
            if self._check_termination(_mxiter):
                break

        sol = self.get_solution()
        sol.set_lb(self.get_lb())

        inc_problem = self.problem
        if self.incumbent is not None:
            inc_problem = self.incumbent.problem

        res = SearchResults(sol, inc_problem)
        return res

    cpdef void reset(self):
        """Reset the search state for a fresh solve.

        Clears the queue, incumbent, bound node, and root so that the
        next call to ``solve()`` starts from scratch.
        """
        self._restart_search()
        self.root = None
        self.explored = 0

    cdef void _do_iter(BranchAndBound self, Node node):
        # Lower bound is accepted
        if node.lb < self.get_ub():
            # Node is valid for evaluation
            self.explored += 1
            # Node satisfies all constraints
            self._feasibility_check(node)
        else:
            self.fathom(node)

    cpdef void enqueue(BranchAndBound self, Node node):
        """Include new node into the manager.

        Parameters
        ----------
        node : Node
            Node to be included
        """
        self.manager.enqueue(node)

    cpdef Node dequeue(BranchAndBound self):
        """Chooses the next evaluated node and computes its lower bound.

        Returns
        -------
        Node
            Node to be evaluated
        """
        return self.manager.dequeue()

    cpdef void _warmstart(
        BranchAndBound self,
        Problem warmstart_problem,
    ):
        cdef:
            double lb
            Node node

        if warmstart_problem is not None:
            if warmstart_problem.solution.status == OptStatus.NO_SOLUTION:
                warmstart_problem.compute_bound()
            node = init_node(warmstart_problem)
            if node.lb < self.get_ub():
                self._feasibility_check(node)
                self.log_row('Warmstart')

    cpdef void branch(BranchAndBound self, Node node):
        """From a given node, create children nodes and enqueue them

        Parameters
        ----------
        node : Node
            Node being evaluated
        """
        cdef:
            list[Node] children
            Node child

        children = node.branch()
        if children:
            for child in children:
                self._enqueue_core(child)
        if not self.save_tree and node is not self.root:
            node.cleanup()
            del node

    cpdef void primal_heuristic(BranchAndBound self, Node node):
        """Calls `Problem` `primal_heuristic()` via node
        entity to generate a feasible
        solution from the current node, if any.

        NOTE: By default this is never called in the search tree.
        It is intended to be called from a custom callback.

        Parameters
        ----------
        node : Node
            Node being evaluated
        """
        cdef:
            Node child

        child = node.primal_heuristic()
        if child is None:
            return
        if child.lb < self.get_ub():
            self.log_row('Primal heuristic')
            self.set_solution(child)

    cpdef void upgrade_bound(BranchAndBound self, Node node):
        """Calls `Problem` `stronger_bound()` via node
        entity to generate a better lower bound from the current node,
        if any.

        NOTE: By default this is never called in the search tree.
        It is intended to be called from a custom callback.

        Parameters
        ----------
        node : Node
            Node being evaluated
        """
        node.upgrade_bound()

    cpdef void fathom(BranchAndBound self, Node node):
        """Fathom node (by default is not deleted)

        If deletion is required for managing memory, remember to delete
        node from parent `children` attribute

        Parameters
        ----------
        node : Node
            Node to be fathomed
        """
        node.fathom()
        if not self.save_tree and node is not self.root:
            node.cleanup()
            del node

    cpdef void pre_eval_callback(BranchAndBound self, Node node):
        """Abstraction for callbacks before node bound evaluation"""
        pass

    cpdef void post_eval_callback(BranchAndBound self, Node node):
        """Abstraction for callbacks after node bound evaluation"""
        pass

    cpdef void enqueue_callback(BranchAndBound self, Node node):
        """Abstraction for callbacks after node is enqueued"""
        pass

    cpdef void dequeue_callback(BranchAndBound self, Node node):
        """Abstraction for callbacks after node is dequeued"""
        pass

    cpdef void solution_callback(BranchAndBound self, Node node):
        """
        Abstraction for callback when a candidate
        feasible solution is verified (before being set)
        """
        pass

    cpdef void _enqueue_root(BranchAndBound self):
        self.root = init_node(self.problem)
        self._enqueue_core(self.root)
        self._update_bound()
        self.explored = 0

    cpdef void _node_eval(BranchAndBound self, Node node):
        self.pre_eval_callback(node)
        node.compute_bound()
        self.post_eval_callback(node)

    cpdef void _feasibility_check(BranchAndBound self, Node node):
        if node.check_feasible():
            self.set_solution(node)
        # Node might lead to a better solution
        else:
            self.branch(node)

    cpdef void set_solution(BranchAndBound self, Node node):
        """Assigns the current node as incumbent, updates gap and calls
        `solution_callback`

        Parameters
        ----------
        node : Node
            New solution node
        """
        self.incumbent = node
        self.manager.filter_by_lb(node.lb)
        self._update_gap()
        self.log_row('New incumbent')
        self.solution_callback(node)

    cdef void _enqueue_core(BranchAndBound self, Node node):
        if self.eval_in:
            self._node_eval(node)
        if node.lb < self.get_ub():
            self.enqueue_callback(node)
            self.enqueue(node)
        else:
            self.fathom(node)

    cdef Node _dequeue_core(BranchAndBound self):
        node = self.dequeue()
        if self.eval_out:
            self._node_eval(node)
        self.dequeue_callback(node)
        if node.lb >= self.get_ub():
            if node is self.bound_node:
                self._update_bound()
            self.fathom(node)
            return None
        return node

    cdef bool _check_termination(BranchAndBound self, unsigned long long maxiter):
        cdef:
            Solution sol
        if self._optimality_check():
            self.log_row('Optimal')
            sol = self.get_solution()
            sol.set_optimal()
            return True
        # Termination by iteration limit
        elif self.explored >= maxiter:
            self.log_row('Iter Limit')
            return True
        return False

    cdef void _update_bound(BranchAndBound self):
        cdef:
            Node old_bound

        if not self.manager.not_empty():
            if self.incumbent:
                self.bound_node = self.incumbent
            self._update_gap()
            return
        old_bound = self.bound_node
        self.bound_node = self.manager.get_lower_bound()
        if (
            old_bound is None
            or old_bound is self.root
            or self.bound_node.lb > old_bound.lb
        ):
            self._update_gap()
            self.log_row('LB update')

    cpdef void _log_headers(BranchAndBound self):
        self.__logger.log_headers()

    cpdef void log_row(BranchAndBound self, object message):
        """Log a row to the search logger.

        Parameters
        ----------
        message : Any
            Message to log
        """
        gap = f'{(100 * self.gap):.2f}%'
        ub = f'{float(self.get_ub()):^6.4}'
        lb = f'{float(self.get_lb()):^6.4}'
        self.__logger.log_row(self.explored, ub, lb, gap, message)

    cdef void _update_gap(BranchAndBound self):
        if self.get_ub() != LARGE_POS:
            self.gap = abs(self.get_ub() - self.get_lb()) / abs(self.get_ub())

    cdef bool _optimality_check(BranchAndBound self):
        if self.incumbent is not None and not self.manager.not_empty():
            return True
        return (
            self.get_ub() <= self.get_lb() + self.atol or self.gap <= self.rtol
        )


cdef class DepthFirstBnB(BranchAndBound):
    """Depth-first Branch & Bound algorithm.

    Uses :class:`~bnbpy.cython.priqueue.DfsPriQueue` as the node manager.
    """

    def __init__(
        self,
        Problem problem,
        eval_node = 'out',
        save_tree: bool = False,
    ) -> None:
        super().__init__(problem, eval_node, save_tree, DfsPriQueue())


cdef class BreadthFirstBnB(BranchAndBound):
    """Breadth-first Branch & Bound algorithm.

    Uses a :class:`~bnbpy.cython.priqueue.BfsPriQueue` as the node manager.
    """

    def __init__(
        self,
        Problem problem,
        eval_node = 'out',
        save_tree: bool = False,
    ) -> None:
        super().__init__(problem, eval_node, save_tree, BfsPriQueue())


cdef class BestFirstBnB(BranchAndBound):
    """Best-first Branch & Bound algorithm.

    Uses a :class:`~bnbpy.cython.priqueue.BestPriQueue` as the node manager.
    """

    def __init__(
        self,
        Problem problem,
        eval_node = 'out',
        save_tree: bool = False,
    ) -> None:
        super().__init__(problem, eval_node, save_tree, BestPriQueue())


cdef class LifoBnB(BranchAndBound):
    """Branch & Bound with a last-in first-out (LIFO) node manager.

    Uses :class:`~bnbpy.cython.manager.LifoManager` as the node manager.
    Equivalent to a pure stack-based DFS without bound-based tie-breaking.
    """

    def __init__(
        self,
        Problem problem,
        eval_node = 'out',
        save_tree: bool = False,
    ) -> None:
        super().__init__(problem, eval_node, save_tree, LifoManager())


cdef class FifoBnB(BranchAndBound):
    """Branch & Bound with a first-in first-out (FIFO) node manager.

    Uses :class:`~bnbpy.cython.manager.FifoManager` as the node manager.
    Equivalent to a pure queue-based BFS without bound-based tie-breaking.
    """

    def __init__(
        self,
        Problem problem,
        eval_node = 'out',
        save_tree: bool = False,
    ) -> None:
        super().__init__(problem, eval_node, save_tree, FifoManager())


def configure_logfile(
    filename: str, only_messages: bool = True, mode='a', **kwargs
):
    """Configure logfile to write solution INFO messages

    Parameters
    ----------
    filename : str
        Name of target file

    mode : str, optional
        FileHandler writing mode, by default 'a' (append)
    """
    # Set the logging level (for example, DEBUG)
    log.setLevel(logging.INFO)

    # Create a file handler to write log messages to a file
    file_handler = logging.FileHandler(filename, mode=mode, **kwargs)

    # Set the file handler's logging level (if needed)
    file_handler.setLevel(logging.DEBUG)

    # Create a formatter for the log messages
    log_form = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    if only_messages:
        log_form = '%(asctime)s - %(message)s'
    formatter = logging.Formatter(log_form)

    # Attach the formatter to the file handler
    file_handler.setFormatter(formatter)

    # Add the file handler to the logger
    if not log.hasHandlers():
        log.addHandler(file_handler)
