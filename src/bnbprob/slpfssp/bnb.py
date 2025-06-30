from typing import Literal

from bnbprob.slpfssp.cython.problem import PermFlowShop
from bnbpy.node import Node
from bnbpy.search import BranchAndBound

RESTART = 10_000


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

    restart_freq: int
    """Frequency in which restarts from best bound are called"""

    def __init__(
        self,
        rtol: float = 0.0001,
        atol: float = 0.0001,
        eval_node: Literal['in', 'out', 'both'] = 'in',
        save_tree: bool = False,
        restart_freq: int = RESTART,
    ):
        super().__init__(rtol, atol, eval_node, save_tree)
        self.restart_freq = restart_freq

    def _solution_callback(self, node: Node) -> None:
        if not isinstance(node.problem, PermFlowShop):
            return
        new_sol = node.problem.local_search()
        if new_sol is not None:
            # General procedure in case is valid
            if new_sol.is_feasible() and new_sol.lb < node.solution.lb:
                node.set_solution(new_sol)
                node.check_feasible()
                self.set_solution(node)

    def solution_callback(self, node: Node) -> None:
        """Applies local search with best improvement making
        remove-insertion moves."""
        if isinstance(node.problem, PermFlowShop):
            self._solution_callback(node)

    def dequeue(self) -> Node:
        if self.explored % self.restart_freq == 0:
            pri, node = min(self.queue, key=lambda x: x[-1].lb)
            self.queue.remove((pri, node))
            return node
        return super().dequeue()
