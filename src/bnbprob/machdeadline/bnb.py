from bnbpy import BranchAndBound, Node, Problem


class DeadlineLagrangianSearch(BranchAndBound[Problem]):
    def post_eval_callback(self, node: Node) -> None:
        self.primal_heuristic(node)
