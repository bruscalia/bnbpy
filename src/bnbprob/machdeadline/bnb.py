from bnbpy import BranchAndBound, Node

from .lagrangian import LagrangianDeadline


class DeadlineLagrangianSearch(BranchAndBound[LagrangianDeadline]):
    def post_eval_callback(self, node: Node[LagrangianDeadline]) -> None:
        self.primal_heuristic(node)
