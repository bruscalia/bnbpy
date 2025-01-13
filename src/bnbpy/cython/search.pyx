# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libc.math cimport INFINITY

import heapq
import logging
import time
from typing import Any, List, Literal, Optional, Tuple, Union

from bnbpy.cython.node cimport Node
from bnbpy.logger import SearchLogger
from bnbpy.problem import Problem
from bnbpy.solution import Solution

log = logging.getLogger(__name__)


cdef:
    double LARGE_POS = INFINITY
    double LOW_NEG = -INFINITY
    int LARGE_INT = 100000000


cdef class BranchAndBound:
    """Class for solving optimization problems via Branch & Bound"""

    def __init__(
        self,
        rtol: float = 1e-4,
        atol: float = 1e-4,
        eval_node: Literal['in', 'out', 'both'] = 'out',
        save_tree: bool = False
    ) -> None:
        """Instantiate algoritm to solve problems via Branch & Bound

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
        self.problem = None
        self.root = None
        self._restart_search()
        self.rtol = rtol
        self.atol = atol
        self.eval_node = eval_node
        self.explored = 0
        self.eval_in = self.eval_node in {'in', 'both'}
        self.eval_out = self.eval_node in {'out', 'both'}
        self.save_tree = save_tree
        self.incumbent = None
        self.bound_node = None
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

    cdef object get_solution(BranchAndBound self):
        if self.incumbent is not None:
            return self.incumbent.solution
        elif self.bound_node is not None:
            return self.bound_node.solution
        return Solution()

    cpdef void _set_problem(BranchAndBound self, problem: Problem):
        self.problem = problem

    cpdef void _restart_search(BranchAndBound self):
        self.incumbent = None
        self.bound_node = None
        self.gap = LARGE_POS
        self.queue = []

    def solve(
        self,
        problem: Problem,
        maxiter: Optional[int] = None,
        timelimit: Optional[Union[int, float]] = None
    ) -> Optional[Solution]:
        """Solves optimization problem using Branch & Bound

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
        cdef:
            double start_time, current_time
            double _tlim = LARGE_POS
            int _mxiter = LARGE_INT
            Node node

        self._set_problem(problem)
        self._restart_search()
        if maxiter is not None:
            _mxiter = maxiter
        if timelimit is not None:
            _tlim = timelimit
            start_time = time.time()
        log.info('Starting exploration of search tree')
        self._log_headers()
        self._warmstart(solution=problem.warmstart())
        self._solve_root()
        while self.queue:
            # Check for time termination
            if timelimit is not None:
                current_time = time.time()
                if current_time - start_time >= _tlim:
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
        self.solution.set_lb(self.get_lb())
        return self.solution

    cdef void _do_iter(BranchAndBound self, Node node):
        """Do loop iteration using a reference node just dequeued

        Parameters
        ----------
        node : Node
            Candidate node
        """
        # Node is valid for evaluation
        self.explored += 1
        # Lower bound is accepted
        if node.lb < self.get_ub():
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
        heapq.heappush(self.queue, ((-node.level, node.lb), node))

    cpdef Node dequeue(BranchAndBound self):
        """Chooses the next evaluated node and computes its lower bound

        Returns
        -------
        Node
            Node to be evaluated
        """
        cdef:
            Node node
            tuple[object, Node] next_item

        next_item = heapq.heappop(self.queue)
        node = next_item[1]
        return node

    cpdef void _warmstart(
        BranchAndBound self,
        solution: Optional[Solution]
    ):
        """If a warmstart is available, use it to set an upper bound

        Parameters
        ----------
        solution : Optional[Solution], optional
            Initial solution, by default None
        """
        cdef:
            Node node

        if solution is not None:
            node = Node(self.problem.copy())
            node.set_solution(solution)
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

    cpdef void fathom(BranchAndBound self, Node node):  # noqa: PLR6301
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

    cpdef void _solve_root(BranchAndBound self):
        self.root = Node(self.problem, parent=None)
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
        self._update_gap()
        self.log_row('New incumbent')
        self.solution_callback(node)

    cdef void _enqueue_core(BranchAndBound self, Node node):
        if self.eval_in:
            self._node_eval(node)
        self.enqueue_callback(node)
        self.enqueue(node)

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

    cdef bool _check_termination(BranchAndBound self, int maxiter):
        if self._optimality_check():
            self.log_row('Optimal')
            self.solution.set_optimal()
            return True
        # Termination by iteration limit
        elif self.explored >= maxiter:
            self.log_row('Iter Limit')
            return True
        return False

    cdef void _update_bound(BranchAndBound self):
        if len(self.queue) == 0:
            if self.incumbent:
                self.bound_node = self.incumbent
            self._update_gap()
            return
        cdef Node old_bound = self.bound_node
        self.bound_node = min(self.queue, key=_first_element_lb)[1]
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
        gap = f'{(100 * self.gap):.2f}%'
        ub = f'{float(self.get_ub()):^6.4}'
        lb = f'{float(self.get_lb()):^6.4}'
        self.__logger.log_row(self.explored, ub, lb, gap, message)

    cdef void _update_gap(BranchAndBound self):
        if self.get_ub() != LARGE_POS:
            self.gap = abs(self.get_ub() - self.get_lb()) / abs(self.get_ub())

    cdef bool _optimality_check(BranchAndBound self):
        return (
            self.get_ub() <= self.get_lb() + self.atol or self.gap <= self.rtol
        )


cpdef _first_element_lb(tuple[object, Node] x):
    return x[1].lb


class BreadthFirstBnB(BranchAndBound):
    """Breadth-first Branch & Bound algorithm"""

    def enqueue(self, node: Node):
        """Include new node into queue

        Parameters
        ----------
        node : Node
            Node to be included
        """
        heapq.heappush(self.queue, ((node.level, node.lb), node))


class DepthFirstBnB(BranchAndBound):
    """Depth-first Branch & Bound algorithm"""

    # Just an alias
    pass


class BestFirstBnB(BranchAndBound):
    """Relation priority Branch & Bound algorithm"""

    queue: List[Tuple[Any, Node]]

    def __init__(
        self,
        rtol: float = 0.0001,
        atol: float = 0.0001,
        eval_node: Literal['in', 'out', 'both'] = 'in',
        save_tree: bool = False,
    ) -> None:
        super().__init__(rtol, atol, eval_node, save_tree)

    def enqueue(self, node: Node):
        return heapq.heappush(self.queue, ((node.lb, -node.level), node))


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
