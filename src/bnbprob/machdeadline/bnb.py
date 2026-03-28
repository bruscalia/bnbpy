from bnbpy import BranchAndBound, Node


class DeadlineLagrangianSearch(BranchAndBound):
    def post_eval_callback(self, node: Node) -> None:
        self.primal_heuristic(node)
