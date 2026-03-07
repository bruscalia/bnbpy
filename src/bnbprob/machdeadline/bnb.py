from bnbprob.machdeadline.lagrangian import LagrangianDeadline
from bnbpy import BranchAndBound, Node


class DeadlineLagrangianSearch(BranchAndBound):
    def post_eval_callback(self, node: Node) -> None:
        problem = node.problem
        if isinstance(problem, LagrangianDeadline):
            cost = problem.calc_real_cost()
            if cost < self.ub:
                new_sol = problem.warmstart()
                if new_sol is not None:
                    self.log_row('Heuristic')
                    sol_node = Node(new_sol, parent=None)
                    sol_node.compute_bound()
                    sol_node.check_feasible()
                    self.set_solution(sol_node)
