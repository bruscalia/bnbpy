# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

from libc.math cimport INFINITY
from libc.limits cimport ULLONG_MAX
from libcpp cimport bool

import logging
import time
from typing import Any, Optional, Union

from bnbpy.cython.levelqueue cimport CyclicBestSearch
from bnbpy.cython.manager cimport BaseNodeManager, FifoManager, LifoManager
from bnbpy.cython.node cimport Node, init_node
from bnbpy.cython.primanager cimport BestFirstSearch, DepthFirstSearch
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
    *   `enqueue_callback`: Before a node is enqueued
        (after its evaluation, if `eval_node` includes 'in').
    *   `dequeue_callback`: After a node is dequeued
        (and evaluated, if `eval_node` includes 'out').
    *   `solution_callback`: When a new feasible
        solution is obtained (after being set).

    **Core methods:**

    *   `branch`: From a given node, create children nodes and enqueue them.
    *   `prune`: Discard a node that cannot improve the incumbent.
    *   `set_solution`: Set a node as the new incumbent.
    *   `primal_heuristic`: Try a heuristic solution from a node
        (only if called from a callback).
    *   `upgrade_bound`: Try a stronger bound for a node
        (only if called from a callback).

    For a customization of enqueueing and dequeueing strategies,
    pass a custom ``manager`` (subclass of `BaseNodeManager`) at construction
    time, or replace it with :meth:`set_manager`.
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
            Defaults to ``DepthFirstSearch()`` (depth-first search) when
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
        self.manager = manager if manager is not None else DepthFirstSearch()

        # Default tolerances, might be overridden by solve() parameters
        self.rtol = 1e-4
        self.atol = 1e-4

        # Evaluation strategy flags
        if eval_node not in {'in', 'out', 'both'}:
            raise ValueError(
                "eval_node must be one of 'in', 'out' or 'both',"
                f" got {eval_node!r}"
            )
        self.eval_node = eval_node
        self.eval_in = eval_node in {'in', 'both'}
        self.eval_out = eval_node in {'out', 'both'}
        self.save_tree = save_tree

        # Core search attributes
        self.incumbent = None
        self.bound_node = None
        self.gap = INFINITY
        # Logging only (see _update_bound): no bound reported yet
        self._last_lb = LOW_NEG
        self._infeasible = False

        # Initialize logger
        self.logger = SearchLogger(log)

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
        """Upper bound: cost of the incumbent (infinity if none)"""
        return self.get_ub()

    cdef double get_ub(BranchAndBound self):
        if self.incumbent is not None:
            return self.incumbent.lb
        return LARGE_POS

    @property
    def lb(self):
        """Global lower bound of the search"""
        return self.get_lb()

    cdef double get_lb(BranchAndBound self):
        if self._infeasible:
            return LARGE_POS
        if self.bound_node is not None:
            return min(self.bound_node.lb, self.get_ub())
        return LOW_NEG

    @property
    def solution(self):
        """Solution of the incumbent, or a solution with the current
        lower bound if there is no incumbent"""
        return self.get_solution()

    cdef Solution get_solution(BranchAndBound self):
        cdef:
            Solution sol

        if self.incumbent is not None:
            return self.incumbent.get_solution()
        # The bound node might have been cleaned up already,
        # so its problem is never accessed
        sol = Solution()
        if self._infeasible:
            sol.set_lb(LARGE_POS)
            sol.set_infeasible()
        elif self.bound_node is not None:
            sol.set_lb(self.get_lb())
        return sol

    @staticmethod
    def build_manager(strategy: str, **options: Any) -> BaseNodeManager:
        """Factory method that returns a :class:`BaseNodeManager` for the
        given traversal strategy name.

        Parameters
        ----------
        strategy : str
            One of ``'dfs'``, ``'bfs'``, ``'best'``, ``'lifo'``, ``'fifo'``, ``'cbfs'``.

            *   ``'dfs'``  — Depth-first search (``DepthFirstSearch``).
            *   ``'bfs'``  — Breadth-first search (``FifoManager``).
            *   ``'best'`` — Best-first search (``BestFirstSearch``).
            *   ``'lifo'`` — Last-in first-out stack (``LifoManager``).
            *   ``'fifo'`` — First-in first-out queue (``FifoManager``).
            *   ``'cbfs'`` — Cyclic best-first search (``CyclicBestSearch``).

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
        _strategies = {
            'dfs': DepthFirstSearch,
            'bfs': FifoManager,
            'best': BestFirstSearch,
            'lifo': LifoManager,
            'fifo': FifoManager,
            'cbfs': CyclicBestSearch,
        }
        key = strategy.lower()
        if key not in _strategies:
            raise ValueError(
                f"Unknown strategy {strategy!r}. "
                f"Choose from: {list(_strategies)}"
            )
        return _strategies[key](**options)

    cpdef void set_manager(self, BaseNodeManager manager):
        """Set a new node manager for the search.

        Parameters
        ----------
        manager : BaseNodeManager
            The new manager to use for node storage and retrieval.
        """
        self.manager = manager

    cdef void _restart_search(BranchAndBound self):
        self.incumbent = None
        self.bound_node = None
        self.gap = INFINITY
        # Logging only (see _update_bound): report bounds again from scratch
        self._last_lb = LOW_NEG
        self._infeasible = False
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
            Maximum number of additional iterations (explored nodes),
            by default None. With ``maxiter=0`` no node is explored.

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
            Search results containing best solution and problem instance.
            If the search tree is exhausted without any feasible solution,
            the status is ``INFEASIBLE`` (cost and lower bound are infinite).
            If it stops (limits) without any feasible solution, the status
            is ``RELAXATION`` with the current lower bound.

        Raises
        ------
        ValueError
            If ``maxiter`` is negative
        """

        cdef:
            double start_time, current_time
            double _tlim = LARGE_POS
            unsigned long long _mxiter
            Node node
            Solution sol
            Problem inc_problem

        if maxiter is not None and maxiter < 0:
            raise ValueError(f'maxiter must be non-negative, got {maxiter}')

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
        # or no iterations are allowed
        if not self._check_termination(_mxiter):
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
                    # Perform iteration (feasibility, bound check, branching)
                    self._do_iter(node)
                # Update LB if node is the one
                if node is self.bound_node:
                    self._update_bound()
                # Termination by optimality
                if self._check_termination(_mxiter):
                    break

        # Search tree exhausted without any feasible solution
        if (
            self.incumbent is None
            and self.root is not None
            and not self.manager.not_empty()
            and not self._infeasible
        ):
            self._infeasible = True
            self.log_row('Infeasible')

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
            self.prune(node)

    cpdef void _warmstart(
        BranchAndBound self,
        Problem warmstart_problem,
    ):
        cdef:
            Node node

        if warmstart_problem is None:
            return
        if warmstart_problem.solution.status == OptStatus.NO_SOLUTION:
            warmstart_problem.compute_bound()
        node = init_node(warmstart_problem)
        if node.lb >= self.get_ub():
            return
        # Only feasible warmstarts are used; never branched
        if node.check_feasible():
            self.set_solution(node)
            self.log_row('Warmstart')
        else:
            self.log_row('Warmstart infeasible')

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
        elif self.save_tree:
            node.save_children(children)

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

    cpdef void prune(BranchAndBound self, Node node):
        """Prune node. By default `Node.cleanup()` is called, unless
        `save_tree` is set or the node is the root, in which case
        the node is only marked as fathomed (status ``FATHOM``).

        Parameters
        ----------
        node : Node
            Node to be pruned
        """
        if not self.save_tree and node is not self.root:
            node.cleanup()
        else:
            node.fathom()

    cpdef void pre_eval_callback(BranchAndBound self, Node node):
        """Abstraction for callbacks before node bound evaluation"""
        pass

    cpdef void post_eval_callback(BranchAndBound self, Node node):
        """Abstraction for callbacks after node bound evaluation"""
        pass

    cpdef void enqueue_callback(BranchAndBound self, Node node):
        """
        Abstraction for callbacks immediately
        before node is enqueued, already after being evaluated.

        Parameters
        ----------
        node : Node
            Node that is about to be enqueued.
        """
        pass

    cpdef void dequeue_callback(BranchAndBound self, Node node):
        """
        Abstraction for callbacks immediately
        after node is dequeued and possibly evaluated.

        Parameters
        ----------
        node : Node
            Node that was dequeued and evaluated (if `eval_out` is True).
        """
        pass

    cpdef void solution_callback(BranchAndBound self, Node node):
        """
        Abstraction for callback when a new feasible solution
        is found (after being set as incumbent).

        Parameters
        ----------
        node : Node
            New incumbent node.
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
        # If node is the bound node, its lb was updated
        # after being dequeued, so the global bound must be recomputed
        if node is self.bound_node:
            self._update_bound()
        else:
            self._update_gap()
        self.log_row('New incumbent')
        self.solution_callback(node)

    cpdef void set_bound(BranchAndBound self, Node node):
        """Public interface to set a new node as the
        new `bound_node`, which is a readonly attribute.

        Parameters
        ----------
        node : Node
            New bound node
        """
        self.bound_node = node

    cdef void _enqueue_core(BranchAndBound self, Node node):
        if self.eval_in:
            self._node_eval(node)
        if node.lb < self.get_ub():
            self.enqueue_callback(node)
            self.manager.enqueue(node)
        else:
            self.prune(node)

    cdef Node _dequeue_core(BranchAndBound self):
        cdef:
            Node node

        node = self.manager.dequeue()
        if node is None:
            return None
        if self.eval_out:
            self._node_eval(node)
        self.dequeue_callback(node)
        if node.lb >= self.get_ub():
            if node is self.bound_node:
                self._update_bound()
            self.prune(node)
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
            double lb

        if not self.manager.not_empty():
            if self.incumbent is not None:
                self.bound_node = self.incumbent
            self._update_gap()
            return

        old_bound = self.bound_node
        self.bound_node = self.manager.get_lower_bound()
        # The gap is always recomputed: the lb of the previous bound node
        # may have changed after being dequeued (e.g. eval_node='out')
        self._update_gap()
        # Logging only: compare with the last reported value, not with
        # old_bound.lb, which may have been raised in place since then.
        # The first call always logs, even if the bound is still -inf
        lb = self.get_lb()
        if old_bound is None or lb > self._last_lb:
            self._last_lb = lb
            self.log_row('LB update')

    cpdef void _log_headers(BranchAndBound self):
        self.logger.log_headers()

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
        self.logger.log_row(self.explored, ub, lb, gap, message)

    cdef void _update_gap(BranchAndBound self):
        cdef:
            double ub, diff

        ub = self.get_ub()
        if ub == LARGE_POS:
            return
        # The lower bound never exceeds the upper bound
        diff = ub - self.get_lb()
        if diff <= 0.0:
            self.gap = 0.0
        elif ub == 0.0:
            # Relative gap is undefined: only atol can prove optimality
            self.gap = INFINITY
        else:
            self.gap = diff / abs(ub)

    cdef bool _optimality_check(BranchAndBound self):
        if self.incumbent is None:
            return False
        if not self.manager.not_empty():
            return True
        return (
            self.get_ub() <= self.get_lb() + self.atol or self.gap <= self.rtol
        )


cdef class DepthFirstBnB(BranchAndBound):
    """Depth-first Branch & Bound algorithm.

    Uses :class:`~bnbpy.cython.primanager.DepthFirstSearch` as the node manager.
    """

    def __init__(
        self,
        Problem problem,
        eval_node = 'out',
        save_tree: bool = False,
    ) -> None:
        super().__init__(problem, eval_node, save_tree, DepthFirstSearch())


cdef class BreadthFirstBnB(BranchAndBound):
    """Breadth-first Branch & Bound algorithm.

    Uses a :class:`~bnbpy.cython.manager.FifoManager` as the node manager.
    """

    def __init__(
        self,
        Problem problem,
        eval_node = 'out',
        save_tree: bool = False,
    ) -> None:
        super().__init__(problem, eval_node, save_tree, FifoManager())


cdef class BestFirstBnB(BranchAndBound):
    """Best-first Branch & Bound algorithm.

    Uses a :class:`~bnbpy.cython.primanager.BestFirstSearch` as the node manager.
    """

    def __init__(
        self,
        Problem problem,
        eval_node = 'out',
        save_tree: bool = False,
    ) -> None:
        super().__init__(problem, eval_node, save_tree, BestFirstSearch())


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

    only_messages : bool, optional
        Whether to log only time stamp and message (no logger name
        or level), by default True

    mode : str, optional
        FileHandler writing mode, by default 'a' (append)

    **kwargs
        Additional keyword arguments for `logging.FileHandler`
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
