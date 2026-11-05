import pytest
from myfixtures.tree import TreeProblem, random_tree, small_tree, walk

from bnbpy import BranchAndBound, Node
from bnbpy.cython.status import OptStatus
from bnbpy.parallel import ParallelBnB

N_TREES = 20


class _CountingParallelBnB(ParallelBnB):
    def __init__(self, problem: TreeProblem) -> None:
        super().__init__(problem, max_workers=2)
        self.enqueued = 0

    def enqueue_callback(self, node: Node[TreeProblem]) -> None:
        self.enqueued += 1


@pytest.mark.search
class TestParallelBnB:
    @staticmethod
    def test_same_results_as_serial() -> None:
        for seed in range(N_TREES):
            tree = random_tree(seed)
            serial = BranchAndBound(TreeProblem(tree), eval_node='in')
            res_serial = serial.solve()
            parallel = ParallelBnB(TreeProblem(tree), max_workers=3)
            res_parallel = parallel.solve()
            assert res_parallel.cost == tree.optimum
            assert res_parallel.status == res_serial.status
            assert parallel.explored == serial.explored

    @staticmethod
    def test_callbacks_and_pruning() -> None:
        tree = small_tree(feasible=False)
        bnb = _CountingParallelBnB(TreeProblem(tree))
        res = bnb.solve()
        assert res.status == OptStatus.INFEASIBLE
        # The root is enqueued by the base class, children by branch
        assert bnb.enqueued == len(tree.bound)

    @staticmethod
    def test_save_tree() -> None:
        tree = small_tree()
        bnb = ParallelBnB(TreeProblem(tree), save_tree=True)
        bnb.solve()
        assert bnb.root is not None
        assert len(walk(bnb.root)) == len(tree.bound)
