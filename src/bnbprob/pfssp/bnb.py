from bnbpy.node import Node
from bnbpy.search import BranchAndBound


class LazyBnB(BranchAndBound):
    def post_eval_callback(self, node: Node):
        if node.lb < self.ub:
            node.problem.bound_upgrade()
            node.lb = node.problem.lb


class CallbackBnB(LazyBnB):
    def solution_callback(self, node: Node):
        new_sol = node.problem.local_search()
        if new_sol is not None:
            # General procedure in case is valid
            if new_sol.is_feasible() and new_sol.lb < node.solution.lb:
                node.set_solution(new_sol)
                node.check_feasible()
                self.set_solution(node)


class ExpBnB(CallbackBnB):
    def branch(self, node: Node):
        super().branch(node)
        if node.children:
            for child in node.children:
                child.parent = None
        del node

    def fathom(self, node: Node):
        super().fathom(node)
        if node.parent is not None:
            node.parent.children.remove(node)
            node.problem = None
            del node

    def solution_callback(self, node: Node):
        if node.level > 0 or node.problem.constructive != 'neh':
            return super().solution_callback(node)
