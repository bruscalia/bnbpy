from bnbpy import BranchAndBound, Node

from .lagrangian import LagrangianTardiness


class TardinessLagrangianSearch(BranchAndBound[LagrangianTardiness]):
    def post_eval_callback(self, node: Node[LagrangianTardiness]) -> None:
        self.primal_heuristic(node)
