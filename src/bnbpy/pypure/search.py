import heapq
import logging
import time
from typing import Any, List, Literal, Optional, Tuple, Union

from bnbpy.logger import SearchLogger
from bnbpy.pypure.node import Node
from bnbpy.pypure.problem import Problem
from bnbpy.pypure.solution import Solution

log = logging.getLogger(__name__)

LARGE_INT = 100000000
LARGE_POS = float('inf')
LOW_NEG = -float('inf')


class BranchAndBound:
    """Class for solving optimization problems via Branch & Bound"""

    problem: Optional[Problem]
    """Base instance of the problem (as in root node, after initialized)"""
    root: Optional[Node]
    """Root node (after initialized)"""
    gap: float
    """Feasibility gap between lb and ub"""
    queue: List[Tuple[Any, Node]]
    """Queue of nodes to be explored in pairs `(priority, node)`"""
    rtol: float
    """Relative tolerance for termination"""
    atol: float
    """Absolute tolerance for termination"""
    explored: int
    """Number of nodes already explored"""
    eval_in: bool
    """Either or not nodes as evaluated as enqueued"""
    eval_out: bool
    """Either or not nodes are evaluated as dequeued"""
    incumbent: Optional[Node]
    """Node with the current best feasible solution"""
    bound_node: Optional[Node]
    """Node currently holding best bound"""
    __logger = SearchLogger(log)

    def __init__(
        self,
        rtol: float = 1e-4,
        atol: float = 1e-4,
        eval_node: Literal['in', 'out', 'both'] | str = 'out',
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

    @property
    def ub(self) -> float:
        """Upper bound, or best feasible solution found so far"""
        if self.incumbent is not None:
            return self.incumbent.lb
        return LARGE_POS

    @property
    def lb(self) -> float:
        """Lower bound, or best possible solution proven so far"""
        if self.bound_node is not None:
            return min(self.bound_node.lb, self.ub)
        return LOW_NEG

    @property
    def solution(self) -> Solution:
        """Best feasible solution found so far"""
        if self.incumbent is not None:
            return self.incumbent.solution
        elif self.bound_node is not None:
            return self.bound_node.solution
        return Solution()

    def _set_problem(self, problem: Problem) -> None:
        self.problem = problem

    def _restart_search(self) -> None:
        self.incumbent = None
        self.bound_node = None
        self.gap = float('inf')
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
        self._set_problem(problem)
        self._restart_search()
        maxiter = LARGE_INT if maxiter is None else maxiter
        if timelimit is not None:
            start_time = time.time()
        log.info('Starting exploration of search tree')
        self._log_headers()
        self._warmstart(solution=problem.warmstart())
        self._solve_root()
        while self.queue:
            # Check for time termination
            if timelimit is not None:
                current_time = time.time()
                if current_time - start_time >= timelimit:
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
            if self._check_termination(maxiter):
                break
        self.solution.set_lb(self.lb)
        return self.solution

    def _do_iter(self, node: Node) -> None:
        """Do loop iteration using a reference node just dequeued

        Parameters
        ----------
        node : Node
            Candidate node
        """
        # Node is valid for evaluation
        self.explored += 1
        # Lower bound is accepted
        if node.lb < self.ub:
            # Node satisfies all constraints
            self._feasibility_check(node)
        else:
            self.fathom(node)

    def enqueue(self, node: Node) -> None:
        """Include new node into queue

        Parameters
        ----------
        node : Node
            Node to be included
        """
        heapq.heappush(self.queue, ((-node.level, node.lb), node))

    def dequeue(self) -> Node:
        """Chooses the next evaluated node and computes its lower bound

        Returns
        -------
        Node
            Node to be evaluated
        """
        _, node = heapq.heappop(self.queue)
        return node

    def _warmstart(self, solution: Optional[Solution] = None) -> None:
        """If a warmstart is available, use it to set an upper bound

        Parameters
        ----------
        solution : Optional[Solution], optional
            Initial solution, by default None
        """
        if solution and self.problem is not None:
            node = Node(self.problem.copy())
            node.set_solution(solution)
            if node.lb < self.ub:
                self._feasibility_check(node)
                self.log_row('Warmstart')

    def branch(self, node: Node) -> None:
        """From a given node, create children nodes and enqueue them

        Parameters
        ----------
        node : Node
            Node being evaluated
        """
        children = node.branch()
        if children:
            for child in children:
                self._enqueue_core(child)
        else:
            self.log_row('Cutoff')
        if not self.save_tree and node is not self.root:
            node.cleanup()
            del node

    def fathom(self, node: Node) -> None:  # noqa: PLR6301
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

    def pre_eval_callback(self, node: Node) -> None:
        """Abstraction for callbacks before node bound evaluation"""
        pass

    def post_eval_callback(self, node: Node) -> None:
        """Abstraction for callbacks after node bound evaluation"""
        pass

    def enqueue_callback(self, node: Node) -> None:
        """Abstraction for callbacks after node is enqueued"""
        pass

    def dequeue_callback(self, node: Node) -> None:
        """Abstraction for callbacks after node is dequeued"""
        pass

    def solution_callback(self, node: Node) -> None:
        """
        Abstraction for callback when a candidate
        feasible solution is verified (before being set)
        """
        pass

    def _solve_root(self) -> None:
        if self.problem is not None:
            self.root = Node(self.problem, parent=None)
            self._enqueue_core(self.root)
            self._update_bound()
            self.explored = 0
        else:
            raise ValueError(
                'Problem instance is not set. Use `_set_problem` method.'
            )

    def _node_eval(self, node: Node) -> None:
        self.pre_eval_callback(node)
        node.compute_bound()
        self.post_eval_callback(node)

    def _feasibility_check(self, node: Node) -> None:
        if node.check_feasible():
            self.set_solution(node)
        # Node might lead to a better solution
        else:
            self.branch(node)

    def set_solution(self, node: Node) -> None:
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

    def _enqueue_core(self, node: Node) -> None:
        if self.eval_in:
            self._node_eval(node)
        self.enqueue_callback(node)
        self.enqueue(node)

    def _dequeue_core(self) -> Optional[Node]:
        node = self.dequeue()
        if self.eval_out:
            self._node_eval(node)
        self.dequeue_callback(node)
        if node.lb >= self.ub:
            if node is self.bound_node:
                self._update_bound()
            self.fathom(node)
            return None
        return node

    def _check_termination(self, maxiter: int) -> bool:
        if self._optimality_check():
            self.log_row('Optimal')
            self.solution.set_optimal()
            return True
        # Termination by iteration limit
        elif self.explored >= maxiter:
            self.log_row('Iter Limit')
            return True
        return False

    def _update_bound(self) -> None:
        if len(self.queue) == 0:
            if self.incumbent:
                self.bound_node = self.incumbent
            self._update_gap()
            return
        old_bound = self.bound_node
        self.bound_node = min(self.queue, key=lambda x: x[-1].lb)[-1]
        if (
            old_bound is None
            or old_bound is self.root
            or self.bound_node.lb > old_bound.lb
        ):
            self._update_gap()
            self.log_row('LB update')

    def _log_headers(self) -> None:
        self.__logger.log_headers()

    def log_row(self, message: str) -> None:
        gap = f'{(100 * self.gap):.2f}%'
        ub = f'{float(self.ub):^6.4}'
        lb = f'{float(self.lb):^6.4}'
        self.__logger.log_row(self.explored, ub, lb, gap, message)

    def _update_gap(self) -> None:
        if self.ub != float('inf'):
            self.gap = abs(self.ub - self.lb) / abs(self.ub)

    def _optimality_check(self) -> bool:
        return self.ub <= self.lb + self.atol or self.gap <= self.rtol


class BreadthFirstBnB(BranchAndBound):
    """Breadth-first Branch & Bound algorithm"""

    def enqueue(self, node: Node) -> None:
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
    ) -> None:
        super().__init__(rtol, atol, eval_node)

    def enqueue(self, node: Node) -> None:
        return heapq.heappush(self.queue, ((node.lb, -node.level), node))


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
