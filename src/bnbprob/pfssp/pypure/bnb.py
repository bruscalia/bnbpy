from typing import Literal

from bnbprob.pfssp.pypure.problem import PermFlowShop
from bnbpy.pypure.node import Node
from bnbpy.pypure.search import BranchAndBound

RESTART = 10_000


class FSNode(Node):
    """Subclass of `Node` with `problem` attribute as `PermFlowShop`."""

    problem: PermFlowShop


class LazyBnB(BranchAndBound):
    """Subclass derived from `BranchAndBound` with `post_eval_callback`
    that solves a 2M lower bound (`problem.bound_upgrade`)."""

    def __init__(
        self,
        rtol: float = 0.0001,
        atol: float = 0.0001,
        eval_node: str = 'in',
        save_tree: bool = False,
    ):
        super().__init__(rtol, atol, eval_node, save_tree)

    def _post_eval_callback(self, node: FSNode) -> None:
        if node.lb < self.ub:
            node.problem.bound_upgrade()
            node.lb = node.problem.lb

    def post_eval_callback(self, node: Node) -> None:
        if isinstance(node, FSNode):
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
        eval_node: Literal['in', 'out', 'both'] | str = 'in',
        save_tree: bool = False,
        restart_freq: int = RESTART,
    ):
        super().__init__(rtol, atol, eval_node, save_tree)
        self.restart_freq = restart_freq

    def _solution_callback(self, node: FSNode) -> None:
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
        if isinstance(node, FSNode):
            self._solution_callback(node)

    def dequeue(self) -> Node:
        if self.explored % self.restart_freq == 0:
            pri, node = min(self.queue, key=lambda x: x[-1].lb)
            self.queue.remove((pri, node))
            return node
        return super().dequeue()


class CallbackBnBAge(CallbackBnB):
    """Subclass derived from `BranchAndBound` with `post_eval_callback`
    that solves a 2M lower bound (`problem.bound_upgrade`).

    Additionally there's local search as a `solution_callback` and
    a best bound guided search restart at each `restart_freq` nodes
    since last solution."""

    sol_age: int
    """Frequency in which restarts from best bound are called"""

    def __init__(
        self,
        rtol: float = 0.0001,
        atol: float = 0.0001,
        eval_node: Literal['in', 'out', 'both'] | str = 'in',
        save_tree: bool = False,
        restart_freq: int = RESTART,
    ):
        super().__init__(rtol, atol, eval_node, save_tree, restart_freq)
        self.sol_age = 0

    def dequeue(self) -> Node:
        self.sol_age += 1
        if (self.sol_age % self.restart_freq) == 0:
            pri, node = min(self.queue, key=lambda x: x[-1].lb)
            self.queue.remove((pri, node))
            return node
        return super().dequeue()
