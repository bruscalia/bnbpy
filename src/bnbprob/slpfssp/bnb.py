from math import sqrt
from typing import Literal

from bnbprob.slpfssp.cython.priqueue import DFSPriQueueFS
from bnbprob.slpfssp.cython.problem import PermFlowShop
from bnbprob.slpfssp.cython.solution import FlowSolution
from bnbpy.node import Node
from bnbpy.search import BranchAndBound

HEUR_BASE = 100


class LazyBnB(BranchAndBound):
    """Subclass derived from `BranchAndBound` with `post_eval_callback`
    that solves a 2M lower bound (`problem.bound_upgrade`)."""

    def __init__(
        self,
        rtol: float = 0.0001,
        atol: float = 0.0001,
        eval_node: Literal['in', 'out', 'both'] = 'in',
        save_tree: bool = False,
    ):
        super().__init__(rtol, atol, eval_node, save_tree)
        self.queue = DFSPriQueueFS()

    def _post_eval_callback(self, node: Node) -> None:
        if not isinstance(node.problem, PermFlowShop):
            return
        if node.lb < self.ub:
            node.problem.bound_upgrade()
            node.lb = node.problem.lb

    def post_eval_callback(self, node: Node) -> None:
        if isinstance(node.problem, PermFlowShop):
            self._post_eval_callback(node)


class CallbackBnB(LazyBnB):
    """Subclass derived from `BranchAndBound` with `post_eval_callback`
    that solves a 2M lower bound (`problem.bound_upgrade`).

    Additionally there's local search as a `solution_callback` and
    a best bound guided search restart at each `restart_freq` nodes."""

    base_heur_factor: int
    """Frequency in which intensification is applied at start"""
    heur_factor: int
    """Frequency in which intensification is applied after each restart"""
    heur_calls: int
    """Number of heuristic calls regularized by success factors"""

    def __init__(
        self,
        rtol: float = 0.0001,
        atol: float = 0.0001,
        eval_node: Literal['in', 'out', 'both'] = 'in',
        save_tree: bool = False,
        heur_factor: int = HEUR_BASE
    ) -> None:
        super(CallbackBnB, self).__init__(rtol, atol, eval_node, save_tree)
        self.queue = DFSPriQueueFS()
        self.base_heur_factor = heur_factor
        self.heur_factor = heur_factor
        self.heur_calls = 0
        self.level_restart = 0

    def solution_callback(self, node: Node) -> None:

        problem: PermFlowShop = node.problem
        new_sol = problem.local_search()
        if new_sol is not None:
            # General procedure in case is valid
            if new_sol.is_feasible() and new_sol.lb < node.lb:
                node.set_solution(new_sol)
                node.check_feasible()
                self.set_solution(node)

    def dequeue(self) -> Node:
        node = self.queue.dequeue()
        if (
            self.explored >= self.heur_factor or node is self.bound_node
        ):
            self.intensify(node)
        return node

    def intensify(self, node: Node) -> None:
        new_node: Node
        problem: PermFlowShop
        ref_problem: PermFlowShop
        new_sol: FlowSolution

        problem = node.problem
        if self.explored >= 1:
            # Sort free jobs according to
            # corresponding order in incumbent solution
            if self.incumbent is not None:
                ref_problem = self.incumbent.problem
                new_sol = problem.intensification_ref(
                    ref_problem.solution
                )
            # new_sol = problem.intensification()
            if new_sol.lb < self.ub:
                new_node = Node(problem.copy())
                new_node.set_solution(new_sol)
                self.log_row("Intensification")
                self.set_solution(new_node)
                # Reduce the heuristic wait iterations factor
                self.heur_calls = int(sqrt(self.heur_calls))
            else:
                self.heur_calls += 1
            self.heur_factor = (
                self.explored + self.base_heur_factor * self.heur_calls
            )
