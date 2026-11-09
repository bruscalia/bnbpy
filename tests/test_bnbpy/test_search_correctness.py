"""End-to-end correctness of the search against brute force on explicit
random trees, for every node manager and evaluation mode, plus edge cases
of the search loop (infeasibility, limits, warmstart, callbacks)."""

from typing import Callable, Literal, Optional

import matplotlib
import pytest
from myfixtures.tree import Tree, TreeProblem, random_tree, small_tree, walk

from bnbpy import BranchAndBound, Node, plot_tree
from bnbpy.cython.levelqueue import CyclicBestSearch, DfsPriority
from bnbpy.cython.manager import BaseNodeManager, LifoManager
from bnbpy.cython.status import OptStatus

INF = float('inf')
N_TREES = 25
EvalNode = Literal['in', 'out', 'both']


MANAGERS: dict[str, Callable[[], BaseNodeManager[TreeProblem]]] = {
    'dfs': lambda: BranchAndBound.build_manager('dfs'),
    'bfs': lambda: BranchAndBound.build_manager('bfs'),
    'best': lambda: BranchAndBound.build_manager('best'),
    'lifo': lambda: BranchAndBound.build_manager('lifo'),
    'fifo': lambda: BranchAndBound.build_manager('fifo'),
    'cbfs': lambda: BranchAndBound.build_manager('cbfs'),
    # Enters and leaves the fallback mode during the search
    'cbfs-small': lambda: CyclicBestSearch(max_size=2),
    'cbfs-fallback': lambda: CyclicBestSearch(
        max_size=-1, permanent_fallback=True
    ),
    'dfs-priority': DfsPriority,
}


@pytest.mark.search
@pytest.mark.integration
class TestBruteForce:
    @staticmethod
    @pytest.mark.parametrize('save_tree', [False, True])
    @pytest.mark.parametrize('eval_node', ['in', 'out', 'both'])
    @pytest.mark.parametrize('manager', list(MANAGERS))
    def test_random_trees(
        manager: str, eval_node: EvalNode, save_tree: bool
    ) -> None:
        for seed in range(N_TREES):
            tree = random_tree(seed)
            bnb = BranchAndBound(
                TreeProblem(tree),
                eval_node=eval_node,
                save_tree=save_tree,
                manager=MANAGERS[manager](),
            )
            res = bnb.solve()
            msg = f'seed {seed}: {res} (optimum {tree.optimum})'
            assert res.cost == tree.optimum, msg
            assert res.lb == tree.optimum, msg
            assert bnb.lb == tree.optimum, msg
            if tree.optimum < INF:
                assert res.status == OptStatus.OPTIMAL, msg
                assert bnb.gap == 0.0, msg
            else:
                assert res.status == OptStatus.INFEASIBLE, msg
                assert bnb.solution.status == OptStatus.INFEASIBLE, msg
            if save_tree:
                # Saved tree keeps every node with its problem and links
                assert bnb.root is not None
                nodes = walk(bnb.root)
                assert all(n.problem is not None for n in nodes), msg


class LeafProblem(TreeProblem):
    """Counts calls to `branch` per tree index."""

    calls: dict[int, int] = {}

    def branch(self) -> list['TreeProblem']:
        LeafProblem.calls[self.idx] = LeafProblem.calls.get(self.idx, 0) + 1
        children = self.tree.children[self.idx]
        return [LeafProblem(self.tree, c) for c in children]


class _CountingBnB(BranchAndBound[TreeProblem]):
    def __init__(self, problem: TreeProblem, eval_node: EvalNode) -> None:
        super().__init__(problem, eval_node=eval_node)
        self.enqueued = 0
        self.dequeued = 0

    def enqueue_callback(self, node: Node[TreeProblem]) -> None:
        self.enqueued += 1

    def dequeue_callback(self, node: Node[TreeProblem]) -> None:
        self.dequeued += 1


@pytest.mark.core
@pytest.mark.search
class TestSearchEdgeCases:
    @staticmethod
    def test_wrong_answer_regression() -> None:
        """root -> A (bound 5, feasible), B (bound 1) -> B1 (feasible 2).
        With eval_node='out', evaluating the bound node A used to leave a
        stale zero gap, stopping before B was explored."""
        tree = Tree(
            bound=[0.0, 5.0, 1.0, 2.0],
            feasible=[False, True, False, True],
            children=[[1, 2], [], [3], []],
        )
        for strategy in ['bfs', 'fifo', 'best']:
            for _ in range(10):
                bnb = BranchAndBound(
                    TreeProblem(tree),
                    manager=BranchAndBound.build_manager(strategy),
                )
                res = bnb.solve()
                assert res.cost == tree.optimum
                assert res.lb == tree.optimum

    @staticmethod
    @pytest.mark.parametrize('eval_node', ['in', 'out', 'both'])
    def test_infeasible_tree(eval_node: EvalNode) -> None:
        bnb = BranchAndBound(
            TreeProblem(small_tree(feasible=False)), eval_node=eval_node
        )
        res = bnb.solve()
        assert res.status == OptStatus.INFEASIBLE
        assert res.cost == INF
        assert res.lb == INF
        assert bnb.explored == len(small_tree().bound)
        # Solving again after exhaustion keeps the same result
        res = bnb.solve()
        assert res.status == OptStatus.INFEASIBLE
        assert bnb.solution.status == OptStatus.INFEASIBLE

    @staticmethod
    def test_infeasible_root_without_children() -> None:
        tree = Tree([1.0], [False], [[]])
        res = BranchAndBound(TreeProblem(tree)).solve()
        assert res.status == OptStatus.INFEASIBLE
        assert res.lb == INF

    @staticmethod
    def test_branch_returns_none() -> None:
        class NoneBranch(TreeProblem):
            def branch(self) -> None:  # type: ignore[override]  # noqa: PLR6301
                return None

        res = BranchAndBound(NoneBranch(small_tree())).solve()
        assert res.status == OptStatus.INFEASIBLE

    @staticmethod
    def test_root_feasible() -> None:
        tree = Tree([3.0], [True], [[]])
        bnb = BranchAndBound(TreeProblem(tree))
        res = bnb.solve()
        assert res.status == OptStatus.OPTIMAL
        assert res.cost == tree.bound[0]
        assert bnb.explored == 1

    @staticmethod
    def test_optimal_warmstart() -> None:
        tree = small_tree()

        class Warm(TreeProblem):
            def warmstart(self) -> Optional[TreeProblem]:
                return TreeProblem(self.tree, 3)

        # Root bound equal to the warmstart cost: nothing to explore
        tree.bound[0] = tree.bound[3]
        bnb = BranchAndBound(Warm(tree))
        res = bnb.solve()
        assert res.status == OptStatus.OPTIMAL
        assert res.cost == tree.bound[3]
        assert bnb.explored == 0

    @staticmethod
    def test_infeasible_warmstart_is_ignored() -> None:
        tree = small_tree()

        class Warm(LeafProblem):
            def warmstart(self) -> Optional[TreeProblem]:
                # Infeasible partial solution with children
                return LeafProblem(self.tree, 2)

        LeafProblem.calls = {}
        bnb = BranchAndBound(Warm(tree))
        res = bnb.solve()
        assert res.cost == tree.optimum
        # Node 2 is branched once, in the regular search only
        assert LeafProblem.calls[2] == 1
        LeafProblem.calls = {}
        ref = BranchAndBound(LeafProblem(tree))
        ref.solve()
        assert bnb.explored == ref.explored

    @staticmethod
    def test_timelimit_zero() -> None:
        bnb = BranchAndBound(TreeProblem(small_tree()))
        res = bnb.solve(timelimit=0)
        assert bnb.explored == 0
        assert res.status == OptStatus.RELAXATION

    @staticmethod
    def test_maxiter_zero() -> None:
        bnb = BranchAndBound(TreeProblem(small_tree()))
        res = bnb.solve(maxiter=0)
        assert bnb.explored == 0
        assert res.status == OptStatus.RELAXATION
        # Resuming completes the search
        res = bnb.solve()
        assert res.status == OptStatus.OPTIMAL

    @staticmethod
    def test_negative_maxiter() -> None:
        bnb = BranchAndBound(TreeProblem(small_tree()))
        with pytest.raises(ValueError, match='maxiter'):
            bnb.solve(maxiter=-1)

    @staticmethod
    def test_invalid_eval_node() -> None:
        with pytest.raises(ValueError, match='eval_node'):
            BranchAndBound(TreeProblem(small_tree()), eval_node='inn')  # type: ignore[arg-type]
        bnb = BranchAndBound(TreeProblem(small_tree()), eval_node='both')
        assert bnb.eval_node == 'both'
        assert bnb.eval_in
        assert bnb.eval_out

    @staticmethod
    @pytest.mark.parametrize('tol', ['rtol', 'atol'])
    def test_tolerance_stops_early(tol: str) -> None:
        # root -> B (bound 10) -> chain of infeasible nodes (bound 10.1),
        # A (feasible, cost 10.5): with LIFO, A is explored first
        n = 20
        tree = Tree([10.0, 10.0, 10.5], [False, False, True], [[1, 2], [], []])
        prev = 1
        for _ in range(n):
            tree.bound.append(10.1)
            tree.feasible.append(False)
            tree.children.append([])
            tree.children[prev].append(len(tree.bound) - 1)
            prev = len(tree.bound) - 1
        exact = BranchAndBound(
            TreeProblem(tree), eval_node='in', manager=LifoManager()
        )
        exact.solve(rtol=0.0, atol=0.0)
        assert exact.explored == len(tree.bound)
        loose = BranchAndBound(
            TreeProblem(tree), eval_node='in', manager=LifoManager()
        )
        res = loose.solve(**{tol: 0.5})
        assert res.status == OptStatus.OPTIMAL
        assert res.cost == tree.bound[2]
        assert loose.explored < exact.explored

    @staticmethod
    @pytest.mark.parametrize('eval_node', ['in', 'out', 'both'])
    def test_enqueue_dequeue_callbacks(eval_node: EvalNode) -> None:
        tree = small_tree(feasible=False)
        bnb = _CountingBnB(TreeProblem(tree), eval_node)
        bnb.solve()
        # Nothing is pruned: every node is enqueued and dequeued once
        assert bnb.enqueued == len(tree.bound)
        assert bnb.dequeued == len(tree.bound)

    @staticmethod
    def test_set_manager() -> None:
        bnb = BranchAndBound(TreeProblem(small_tree()))
        manager: LifoManager[TreeProblem] = LifoManager()
        bnb.set_manager(manager)
        assert bnb.manager is manager
        assert bnb.solve().cost == small_tree().optimum

    @staticmethod
    def test_build_manager_options() -> None:
        max_size = 7
        manager = BranchAndBound.build_manager('cbfs', max_size=max_size)
        assert isinstance(manager, CyclicBestSearch)
        assert manager.max_size == max_size

    @staticmethod
    def test_save_tree_with_pruning(monkeypatch: pytest.MonkeyPatch) -> None:
        """Nodes discarded when a new incumbent is found are kept in the
        saved tree, marked as fathomed, and the tree can be plotted."""
        tree = small_tree()
        bnb = BranchAndBound(
            TreeProblem(tree),
            eval_node='in',
            save_tree=True,
            manager=BranchAndBound.build_manager('dfs'),
        )
        bnb.solve()
        assert bnb.root is not None
        nodes = walk(bnb.root)
        assert len(nodes) == len(tree.bound)
        assert all(n.problem is not None for n in nodes)
        statuses = {n.problem.idx: n.solution.status for n in nodes}
        # DFS explores b -> e (cost 4) first, then a -> c (cost 2);
        # d (cost 3) is discarded when c becomes the incumbent
        assert statuses[5] == OptStatus.FEASIBLE
        assert statuses[3] == OptStatus.OPTIMAL
        assert statuses[4] == OptStatus.FATHOM
        matplotlib.use('Agg')
        monkeypatch.setattr('matplotlib.pyplot.show', lambda: None)
        plot_tree(bnb.root)
