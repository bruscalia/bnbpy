# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libc.math cimport INFINITY
from libcpp cimport bool
from libcpp.string cimport string

import heapq
import logging
import time
from typing import Any, List, Literal, Optional, Tuple, Union

from bnbpy.cython.node cimport Node, init_node
from bnbpy.cython.priqueue cimport (
    BasePriQueue,
    BestPriQueue,
    BFSPriQueue,
    DFSPriQueue,
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

    *   `BreadthFirstBnB`: Breadth-first Branch & Bound algorithm.
    *   `DepthFirstBnB`: Depth-first Branch & Bound algorithm
        (alias of `BranchAndBound`).
    *   `BestFirstBnB`: Best-first Branch & Bound algorithm.

    Useful methods for subclassing and custom implementations:

    **Callback methods:**

    *   `pre_eval_callback`: Before node bound evaluation.
    *   `post_eval_callback`: After node bound evaluation.
    *   `enqueue_callback`: After node is enqueued.
    *   `dequeue_callback`: After node is dequeued.
    *   `solution_callback`: When a new feasible
        solution is obtained (after being set).

    **Core methods:**

    *   `enqueue`: Include new node into queue.
    *   `dequeue`: Chooses the next evaluated
        node and computes its lower bound.
    *   `branch`: From a given node, create children nodes and enqueue them.

    For a customization of enqueueing and dequeueing strategies,
    it is recommended subclassing `BranchAndBound` with a customized `queue`
    attribute by subclassing `BasePriQueue` too.
    """

    def __init__(
        self,
        rtol: float = 1e-4,
        atol: float = 1e-4,
        eval_node = 'out',
        save_tree: bool = False
    ) -> None:
        """Instantiate algorithm to solve problems via Branch & Bound.

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
            Node bound evaluation strategy, by default 'out'.

            *   'in': call `Problem.calc_bound` after
                parent `branch`, before inserting child nodes
                in the active queue. Useful when
                bound computation is inexpensive.

            *   'out': call `Problem.calc_bound` after
                selecting a node from the active queue.
                The result guides whether to explore
                (`is_feasible`, possibly `branch`) or
                prune. Often paired with fast enqueue
                proxies for node quality, such as MILP
                pseudo-costs.

            *   'both': evaluate in both moments above.

        save_tree : bool, optional
            Whether to save node relationships, by default False.
            It can consume a lot of memory in large trees.
        """
        self.problem = None
        self.root = None
        self.rtol = rtol
        self.atol = atol
        self.eval_node = <string> eval_node.encode("utf-8")
        self.explored = 0
        self.eval_in = self.eval_node in {'in', 'both'}
        self.eval_out = self.eval_node in {'out', 'both'}
        self.save_tree = save_tree
        self.incumbent = None
        self.bound_node = None
        self.queue = DFSPriQueue()
        self.gap = INFINITY
        self.__logger = SearchLogger(log)

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

    cdef void _set_problem(BranchAndBound self, Problem problem):
        self.problem = problem

    cdef void _restart_search(BranchAndBound self):
        self.incumbent = None
        self.bound_node = None
        self.gap = INFINITY
        self.queue.clear()

    def solve(
        self,
        problem: Problem,
        maxiter: Optional[int] = None,
        timelimit: Optional[Union[int, float]] = None
    ) -> SearchResults:
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

        cdef:
            double start_time, current_time
            double _tlim = LARGE_POS
            unsigned long long _mxiter = ULLONG_MAX
            Node node
            Solution sol
            Problem inc_problem

        # Set limits
        if maxiter is not None:
            _mxiter = maxiter
        if timelimit is not None:
            _tlim = timelimit
        start_time = time.time()

        # Core initialization
        self._restart_search()
        log.info('Starting exploration of search tree')
        self._log_headers()
        self._warmstart(problem.warmstart())
        self._enqueue_root(problem)

        # In case the root node is already the LB of a optimal warmstart
        self._check_termination(_mxiter)
        while self.queue.not_empty():
            # Check for time termination
            if timelimit is not None:
                current_time = time.time()
                if current_time - start_time >= _tlim:
                    self.log_row('Time Limit')
                    break
            node = self._dequeue_core()
            # Avoid node with poor parents in case ub was updated meanwhile
            if node is not None:
                # Perform iteration (feasibility, bound check, and branching)
                self._do_iter(node)
            # Update LB is node is the one
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
        """Include new node into queue

        Parameters
        ----------
        node : Node
            Node to be included
        """
        self.queue.enqueue(node)

    cpdef Node dequeue(BranchAndBound self):
        """Chooses the next evaluated node and computes its lower bound

        Returns
        -------
        Node
            Node to be evaluated
        """
        return self.queue.dequeue()

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
        else:
            self.log_row('Cutoff')
        if not self.save_tree and node is not self.root:
            node.cleanup()
            del node

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

    cpdef void _enqueue_root(BranchAndBound self, Problem problem):
        self.root = init_node(problem)
        self._set_problem(problem)
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
        self.queue.filter_by_lb(node.lb)
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

        if not self.queue.not_empty():
            if self.incumbent:
                self.bound_node = self.incumbent
            self._update_gap()
            return
        old_bound = self.bound_node
        self.bound_node = self.queue.get_lower_bound()
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
        if self.incumbent is not None and not self.queue.not_empty():
            return True
        return (
            self.get_ub() <= self.get_lb() + self.atol or self.gap <= self.rtol
        )


cdef class BreadthFirstBnB(BranchAndBound):

    def __init__(
        self,
        rtol: float = 0.0001,
        atol: float = 0.0001,
        eval_node = 'out',
        save_tree: bool = False,
    ) -> None:
        super().__init__(rtol, atol, eval_node, save_tree)
        self.queue = BFSPriQueue()


cdef class DepthFirstBnB(BranchAndBound):
    # Just an alias
    pass


cdef class BestFirstBnB(BranchAndBound):

    def __init__(
        self,
        rtol: float = 0.0001,
        atol: float = 0.0001,
        eval_node = 'out',
        save_tree: bool = False,
    ) -> None:
        super().__init__(rtol, atol, eval_node, save_tree)
        self.queue = BestPriQueue()


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
