from bnbpy.cython.node import Node
from bnbpy.search import BranchAndBound

RESTART = 10_000


class LazyBnB(BranchAndBound):
    def __init__(
        self, rtol=0.0001, atol=0.0001, eval_node='in', save_tree=False
    ):
        super().__init__(rtol, atol, eval_node, save_tree)

    def post_eval_callback(self, node: Node):
        if node.lb < self.ub:
            node.problem.bound_upgrade()
            node.lb = node.problem.lb


class CallbackBnB(LazyBnB):

    restart_freq: int
    """Frequency in which restarts from best bound are called"""

    def __init__(
        self,
        rtol=0.0001,
        atol=0.0001,
        eval_node='in',
        save_tree=False,
        restart_freq=RESTART,
    ):
        super().__init__(rtol, atol, eval_node, save_tree)
        self.restart_freq = restart_freq

    def solution_callback(self, node: Node):
        new_sol = node.problem.local_search()
        if new_sol is not None:
            # General procedure in case is valid
            if new_sol.is_feasible() and new_sol.lb < node.solution.lb:
                node.set_solution(new_sol)
                node.check_feasible()
                self.set_solution(node)

    def dequeue(self) -> Node:
        if self.explored % self.restart_freq == 0:
            pri, node = min(self.queue, key=lambda x: x[-1].lb)
            self.queue.remove((pri, node))
            return node
        return super().dequeue()


class CallbackBnBAge(LazyBnB):

    restart_freq: int
    """Number of nodes dequeued since last improvement"""
    sol_age: int
    """Frequency in which restarts from best bound are called"""

    def __init__(
        self,
        rtol=0.0001,
        atol=0.0001,
        eval_node='in',
        save_tree=False,
        restart_freq=RESTART,
    ):
        super().__init__(rtol, atol, eval_node, save_tree)
        self.restart_freq = restart_freq
        self.sol_age = 0

    def solution_callback(self, node: Node):
        self.sol_age = 0
        new_sol = node.problem.local_search()
        if new_sol is not None:
            # General procedure in case is valid
            if new_sol.is_feasible() and new_sol.lb < node.solution.lb:
                node.set_solution(new_sol)
                node.check_feasible()
                self.set_solution(node)

    def dequeue(self) -> Node:
        self.sol_age += 1
        if (self.sol_age % self.restart_freq) == 0:
            pri, node = min(self.queue, key=lambda x: x[-1].lb)
            self.queue.remove((pri, node))
            return node
        return super().dequeue()
