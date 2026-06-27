import pytest
from myfixtures.myproblem import MyProblem

from bnbpy.cython.levelqueue import (
    CyclicBestSearch,
    DfsPriority,
    LevelManagerInterface,
    LevelQueue,
)
from bnbpy.cython.node import Node
from bnbpy.cython.primanager import BestFirstSearch, PriorityManagerTemplate
from bnbpy.cython.search import BranchAndBound
from bnbpy.cython.status import OptStatus

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
LB_LOW = 5
LB_MEDIUM = 10
LB_HIGH = 15
LB_VERY_HIGH = 20
MAX_LB_FILTER = 12
TWO = 2
THREE = 3
FOUR = 4
FIVE = 5
NEW_LEVEL = 3


SIX = 6


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
def _make_node(
    lb: float,
    *,
    level: int = 0,
    parent: Node[MyProblem] | None = None,
) -> Node[MyProblem]:
    """Create a node with computed bound and a specific level."""
    problem = MyProblem(lb_value=lb, feasible=False)
    node = Node(problem, parent=parent)
    node.compute_bound()
    node.level = level
    return node


def _make_tree(
    lbs: list[float],
    levels: list[int],
) -> list[Node[MyProblem]]:
    """Create a list of independent nodes from parallel lb/level lists."""
    return [_make_node(lb, level=lvl) for lb, lvl in zip(lbs, levels)]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def queue() -> CyclicBestSearch[MyProblem]:
    return CyclicBestSearch()


@pytest.fixture
def small_queue() -> CyclicBestSearch[MyProblem]:
    """A CyclicBestSearch with a very low max_size for fallback testing."""
    return CyclicBestSearch(max_size=FIVE)


@pytest.fixture
def sticky_small_queue() -> CyclicBestSearch[MyProblem]:
    """A sticky-fallback CyclicBestSearch with low max_size."""
    return CyclicBestSearch(max_size=FIVE, permanent_fallback=True)


@pytest.fixture
def permanent_small_queue() -> CyclicBestSearch[MyProblem]:
    """Alias for sticky_small_queue — permanent-fallback queue."""
    return CyclicBestSearch(max_size=FIVE, permanent_fallback=True)


@pytest.fixture
def dfs_priority() -> DfsPriority[MyProblem]:
    return DfsPriority()


# ---------------------------------------------------------------------------
# LevelQueue
# ---------------------------------------------------------------------------
@pytest.mark.core
@pytest.mark.levelqueue
class TestLevelQueue:
    """Tests for LevelQueue — the per-depth bucket inside level managers."""

    @staticmethod
    def test_initial_state() -> None:
        level: LevelQueue[MyProblem] = LevelQueue(0)
        assert level.level == 0
        assert level.size() == 0

    @staticmethod
    def test_self_linked() -> None:
        """A freshly created level links to itself."""
        level: LevelQueue[MyProblem] = LevelQueue(0)
        assert level.next is level
        assert level.prev is level

    @staticmethod
    def test_add_and_pop_node() -> None:
        level: LevelQueue[MyProblem] = LevelQueue(0)
        node = _make_node(LB_LOW)
        level.push(node)
        assert level.size() == 1
        popped = level.pop()
        assert popped is node
        assert level.size() == 0

    @staticmethod
    def test_pop_empty_returns_none() -> None:
        level: LevelQueue[MyProblem] = LevelQueue(0)
        assert level.pop() is None

    @staticmethod
    def test_best_first_ordering() -> None:
        """LevelQueue uses BestFirstSearch by default — lowest lb first."""
        level: LevelQueue[MyProblem] = LevelQueue(0)
        high = _make_node(LB_HIGH)
        low = _make_node(LB_LOW)
        level.push(high)
        level.push(low)
        assert level.pop() is low
        assert level.pop() is high

    @staticmethod
    def test_make_priority_best_first() -> None:
        """Default make_priority returns (lb, -level, -index) key."""
        level: LevelQueue[MyProblem] = LevelQueue(0)
        high = _make_node(LB_HIGH)
        low = _make_node(LB_LOW)
        level.push(high)
        level.push(low)
        # best-first default: lowest lb dequeued first
        assert level.pop() is low
        assert level.pop() is high

    @staticmethod
    def test_filter_removes_above_threshold() -> None:
        level: LevelQueue[MyProblem] = LevelQueue(0)
        level.push(_make_node(LB_LOW))
        level.push(_make_node(LB_HIGH))
        level.filter(MAX_LB_FILTER)
        assert level.size() == 1
        result = level.pop()
        assert result is not None
        assert result.lb == LB_LOW

    @staticmethod
    def test_class_getitem() -> None:
        """LevelQueue[MyProblem] returns LevelQueue itself."""
        assert LevelQueue[MyProblem] is LevelQueue


# ---------------------------------------------------------------------------
# BestFirstSearch (primanager)
# ---------------------------------------------------------------------------
@pytest.mark.core
@pytest.mark.levelqueue
class TestBestFirstSearch:
    """Tests for BestFirstSearch — the default PriorityManagerInterface."""

    @staticmethod
    def test_enqueue_dequeue() -> None:
        q: BestFirstSearch[MyProblem] = BestFirstSearch()
        node = _make_node(LB_LOW)
        q.enqueue(node)
        assert q.size() == 1
        assert q.dequeue() is node

    @staticmethod
    def test_min_lb_first() -> None:
        q: BestFirstSearch[MyProblem] = BestFirstSearch()
        high = _make_node(LB_HIGH)
        low = _make_node(LB_LOW)
        q.enqueue(high)
        q.enqueue(low)
        assert q.dequeue() is low

    @staticmethod
    def test_get_lower_bound_peek() -> None:
        q: BestFirstSearch[MyProblem] = BestFirstSearch()
        high = _make_node(LB_HIGH)
        low = _make_node(LB_LOW)
        q.enqueue(high)
        q.enqueue(low)
        result = q.get_lower_bound()
        assert result is low
        assert q.size() == TWO  # not removed

    @staticmethod
    def test_filter_by_lb() -> None:
        q: BestFirstSearch[MyProblem] = BestFirstSearch()
        q.enqueue(_make_node(LB_LOW))
        q.enqueue(_make_node(LB_HIGH))
        q.filter_by_lb(MAX_LB_FILTER)
        assert q.size() == 1
        node = q.dequeue()
        assert node is not None
        assert node.lb == LB_LOW

    @staticmethod
    def test_nodecount_increments_on_enqueue() -> None:
        """BestFirstSearch.nodecount tracks enqueue/dequeue."""
        q: BestFirstSearch[MyProblem] = BestFirstSearch()
        node = _make_node(LB_LOW)
        q.enqueue(node)
        assert q.nodecount == 1
        q.dequeue()
        assert q.nodecount == 0

    @staticmethod
    def test_clear_empties_nodecount() -> None:
        """After clear(), nodecount is 0."""
        q: BestFirstSearch[MyProblem] = BestFirstSearch()
        nodes = [_make_node(float(i)) for i in range(FOUR)]
        for n in nodes:
            q.enqueue(n)
        q.clear()
        assert q.size() == 0
        assert q.nodecount == 0

    @staticmethod
    def test_is_priority_manager_template() -> None:
        assert issubclass(BestFirstSearch, PriorityManagerTemplate)


# ---------------------------------------------------------------------------
# CyclicBestSearch — basic state
# ---------------------------------------------------------------------------
@pytest.mark.core
@pytest.mark.levelqueue
class TestCyclicBestSearchBasic:
    """Initialisation, size, not_empty, clear."""

    @staticmethod
    def test_initial_state(queue: CyclicBestSearch[MyProblem]) -> None:
        assert queue.not_empty() is False
        assert queue.size() == 0

    @staticmethod
    def test_not_empty_after_enqueue(
        queue: CyclicBestSearch[MyProblem],
    ) -> None:
        queue.enqueue(_make_node(LB_LOW))
        assert queue.not_empty() is True
        assert queue.size() == 1

    @staticmethod
    def test_clear(queue: CyclicBestSearch[MyProblem]) -> None:
        queue.enqueue(_make_node(LB_LOW))
        queue.enqueue(_make_node(LB_MEDIUM, level=1))
        queue.clear()
        assert queue.not_empty() is False
        assert queue.size() == 0

    @staticmethod
    def test_is_level_manager_interface() -> None:
        assert issubclass(CyclicBestSearch, LevelManagerInterface)


# ---------------------------------------------------------------------------
# CyclicBestSearch — enqueue / dequeue
# ---------------------------------------------------------------------------
@pytest.mark.core
@pytest.mark.levelqueue
class TestCyclicBestSearchEnqueueDequeue:
    """Enqueue and dequeue semantics including round-robin cycling."""

    @staticmethod
    def test_dequeue_empty_returns_none(
        queue: CyclicBestSearch[MyProblem],
    ) -> None:
        assert queue.dequeue() is None

    @staticmethod
    def test_single_node_round_trip(
        queue: CyclicBestSearch[MyProblem],
    ) -> None:
        node = _make_node(LB_LOW)
        queue.enqueue(node)
        assert queue.dequeue() is node
        assert queue.not_empty() is False

    @staticmethod
    def test_same_level_best_first(
        queue: CyclicBestSearch[MyProblem],
    ) -> None:
        """Nodes at the same level are served in best-first order."""
        high = _make_node(LB_HIGH, level=0)
        low = _make_node(LB_LOW, level=0)
        queue.enqueue(high)
        queue.enqueue(low)
        assert queue.dequeue() is low
        assert queue.dequeue() is high

    @staticmethod
    def test_round_robin_across_levels(
        queue: CyclicBestSearch[MyProblem],
    ) -> None:
        """Dequeue cycles through levels in round-robin order."""
        n0a = _make_node(LB_LOW, level=0)
        n0b = _make_node(LB_MEDIUM, level=0)
        n1a = _make_node(LB_LOW, level=1)
        n1b = _make_node(LB_MEDIUM, level=1)

        queue.enqueue(n0a)
        queue.enqueue(n0b)
        queue.enqueue(n1a)
        queue.enqueue(n1b)

        first = queue.dequeue()
        second = queue.dequeue()
        third = queue.dequeue()
        fourth = queue.dequeue()

        assert first is n1a  # advance-first: L0 → L1
        assert second is n0a  # L1 → L0
        assert third is n1b
        assert fourth is n0b

    @staticmethod
    def test_skips_empty_levels(
        queue: CyclicBestSearch[MyProblem],
    ) -> None:
        n0 = _make_node(LB_LOW, level=0)
        n2 = _make_node(LB_LOW, level=2)
        queue.enqueue(n0)
        queue.enqueue(n2)
        first = queue.dequeue()
        second = queue.dequeue()
        assert first is n0
        assert second is n2

    @staticmethod
    def test_levels_expand_on_demand(
        queue: CyclicBestSearch[MyProblem],
    ) -> None:
        deep = _make_node(LB_LOW, level=5)
        queue.enqueue(deep)
        assert len(queue.levels) == SIX
        assert queue.dequeue() is deep

    @staticmethod
    def test_dequeue_advances_to_newly_added_child_level(
        queue: CyclicBestSearch[MyProblem],
    ) -> None:
        root = _make_node(LB_LOW, level=0)
        queue.enqueue(root)
        d0 = queue.dequeue()
        assert d0 is root

        child_a = _make_node(LB_LOW, level=1)
        child_b = _make_node(LB_MEDIUM, level=1)
        queue.enqueue(child_a)
        queue.enqueue(child_b)
        d1 = queue.dequeue()
        assert d1 is not None
        assert d1.level == 1

        grand_a = _make_node(LB_LOW, level=2)
        grand_b = _make_node(LB_MEDIUM, level=2)
        queue.enqueue(grand_a)
        queue.enqueue(grand_b)
        d2 = queue.dequeue()
        assert d2 is not None
        assert d2.level == TWO

        great_a = _make_node(LB_LOW, level=THREE)
        great_b = _make_node(LB_MEDIUM, level=THREE)
        queue.enqueue(great_a)
        queue.enqueue(great_b)
        d3 = queue.dequeue()
        assert d3 is not None
        assert d3.level == THREE


# ---------------------------------------------------------------------------
# CyclicBestSearch — get_lower_bound
# ---------------------------------------------------------------------------
@pytest.mark.core
@pytest.mark.levelqueue
class TestCyclicBestSearchLowerBound:
    @staticmethod
    def test_empty_returns_none(queue: CyclicBestSearch[MyProblem]) -> None:
        assert queue.get_lower_bound() is None

    @staticmethod
    def test_returns_global_minimum(
        queue: CyclicBestSearch[MyProblem],
    ) -> None:
        high = _make_node(LB_HIGH, level=0)
        low = _make_node(LB_LOW, level=1)
        med = _make_node(LB_MEDIUM, level=2)
        queue.enqueue(high)
        queue.enqueue(low)
        queue.enqueue(med)
        result = queue.get_lower_bound()
        assert result is low
        assert queue.size() == THREE

    @staticmethod
    def test_bound_nodes_cleared_when_lower_lb_enqueued(
        queue: CyclicBestSearch[MyProblem],
    ) -> None:
        high = _make_node(LB_HIGH, level=0)
        low = _make_node(LB_LOW, level=0)
        queue.enqueue(high)
        queue.enqueue(low)
        result = queue.get_lower_bound()
        assert result is low
        assert result.lb == LB_LOW

    @staticmethod
    def test_get_lower_bound_remains_valid_after_bound_node_dequeued(
        queue: CyclicBestSearch[MyProblem],
    ) -> None:
        node_a = _make_node(LB_LOW, level=0)
        node_b = _make_node(LB_HIGH, level=0)
        queue.enqueue(node_a)
        queue.enqueue(node_b)
        assert queue.get_lower_bound() is node_a
        dequeued = queue.dequeue()
        assert dequeued is node_a
        result = queue.get_lower_bound()
        assert result is node_b
        assert result.lb == LB_HIGH

    @staticmethod
    def test_nodecount_after_clear(
        queue: CyclicBestSearch[MyProblem],
    ) -> None:
        """LevelManagerInterface: nodecount is 0 after clear()."""
        nodes = [_make_node(float(i), level=i % THREE) for i in range(FIVE)]
        for n in nodes:
            queue.enqueue(n)
        assert queue.nodecount == FIVE
        queue.clear()
        assert queue.size() == 0
        assert queue.nodecount == 0


# ---------------------------------------------------------------------------
# CyclicBestSearch — filter_by_lb
# ---------------------------------------------------------------------------
@pytest.mark.core
@pytest.mark.levelqueue
class TestCyclicBestSearchFilter:
    @staticmethod
    def test_filter_keeps_below(queue: CyclicBestSearch[MyProblem]) -> None:
        queue.enqueue(_make_node(LB_LOW, level=0))
        queue.enqueue(_make_node(LB_MEDIUM, level=1))
        queue.enqueue(_make_node(LB_HIGH, level=2))
        queue.filter_by_lb(MAX_LB_FILTER)
        assert queue.size() == TWO

    @staticmethod
    def test_filter_removes_all(queue: CyclicBestSearch[MyProblem]) -> None:
        queue.enqueue(_make_node(LB_HIGH, level=0))
        queue.enqueue(_make_node(LB_VERY_HIGH, level=1))
        queue.filter_by_lb(LB_LOW)
        assert queue.not_empty() is False

    @staticmethod
    def test_filter_keeps_all(queue: CyclicBestSearch[MyProblem]) -> None:
        queue.enqueue(_make_node(LB_LOW, level=0))
        queue.enqueue(_make_node(LB_MEDIUM, level=1))
        queue.filter_by_lb(LB_VERY_HIGH)
        assert queue.size() == TWO


# ---------------------------------------------------------------------------
# CyclicBestSearch — reset_level
# ---------------------------------------------------------------------------
@pytest.mark.core
@pytest.mark.levelqueue
class TestCyclicBestSearchResetLevel:
    @staticmethod
    def test_reset_rewinds_cycle(queue: CyclicBestSearch[MyProblem]) -> None:
        n0 = _make_node(LB_LOW, level=0)
        n1 = _make_node(LB_LOW, level=1)
        n0b = _make_node(LB_MEDIUM, level=0)
        queue.enqueue(n0)
        queue.enqueue(n1)
        queue.enqueue(n0b)

        first = queue.dequeue()
        assert first is n1

        queue.reset_level()
        second = queue.dequeue()
        assert second is n0


# ---------------------------------------------------------------------------
# CyclicBestSearch — fallback mode
# ---------------------------------------------------------------------------
@pytest.mark.core
@pytest.mark.levelqueue
class TestCyclicBestSearchFallback:
    @staticmethod
    def test_enters_fallback_on_overflow(
        small_queue: CyclicBestSearch[MyProblem],
    ) -> None:
        for i in range(FIVE + TWO):
            small_queue.enqueue(_make_node(float(i), level=0))
        assert small_queue.use_fallback is True

    # @staticmethod
    # def test_dequeue_in_fallback(
    #     small_queue: CyclicBestSearch[MyProblem],
    # ) -> None:
    #     nodes = [_make_node(float(i), level=0) for i in range(FIVE + TWO)]
    #     for n in nodes:
    #         small_queue.enqueue(n)
    #     assert small_queue.use_fallback is True
    #     assert small_queue.dequeue() is not None

    # @staticmethod
    # def test_exits_fallback_after_drain(
    #     small_queue: CyclicBestSearch[MyProblem],
    # ) -> None:
    #     for i in range(FIVE + TWO):
    #         small_queue.enqueue(_make_node(float(i), level=0))
    #     assert small_queue.use_fallback is True
    #     while small_queue.size() > small_queue.max_size // 2:
    #         small_queue.dequeue()
    #     small_queue.dequeue()
    #     assert small_queue.use_fallback is False

    @staticmethod
    def test_fallback_filter_updates_count(
        small_queue: CyclicBestSearch[MyProblem],
    ) -> None:
        for i in range(FIVE + TWO):
            small_queue.enqueue(_make_node(float(i) * 5, level=0))
        small_queue.filter_by_lb(MAX_LB_FILTER)
        for _ in range(small_queue.size()):
            node = small_queue.dequeue()
            assert node is not None
            assert node.lb < MAX_LB_FILTER

    @staticmethod
    def test_permanent_fallback_never_exits(
        permanent_small_queue: CyclicBestSearch[MyProblem],
    ) -> None:
        for i in range(FIVE + TWO):
            permanent_small_queue.enqueue(_make_node(float(i), level=0))
        assert permanent_small_queue.use_fallback is True
        while permanent_small_queue.not_empty():
            permanent_small_queue.dequeue()
        assert permanent_small_queue.use_fallback is True

    @staticmethod
    def test_get_lower_bound_in_fallback(
        small_queue: CyclicBestSearch[MyProblem],
    ) -> None:
        low = _make_node(LB_LOW, level=0)
        for _ in range(FIVE):
            small_queue.enqueue(_make_node(LB_HIGH, level=0))
        small_queue.enqueue(low)
        result = small_queue.get_lower_bound()
        assert result is not None
        assert result.lb == LB_LOW


# ---------------------------------------------------------------------------
# CyclicBestSearch — new_level factory
# ---------------------------------------------------------------------------
@pytest.mark.core
@pytest.mark.levelqueue
class TestCyclicBestSearchNewLevel:
    @staticmethod
    def test_new_level_creates_level_queue(
        queue: CyclicBestSearch[MyProblem],
    ) -> None:
        lvl = queue.new_level(NEW_LEVEL)
        assert isinstance(lvl, LevelQueue)
        assert lvl.level == NEW_LEVEL

    @staticmethod
    def test_new_level_has_empty_queue(
        queue: CyclicBestSearch[MyProblem],
    ) -> None:
        lvl = queue.new_level(0)
        assert lvl.size() == 0


# ---------------------------------------------------------------------------
# DfsPriority
# ---------------------------------------------------------------------------
@pytest.mark.core
@pytest.mark.levelqueue
class TestDfsPriority:
    """Tests for DfsPriority — always-fallback depth-first manager."""

    @staticmethod
    def test_is_level_manager_interface(
        dfs_priority: DfsPriority[MyProblem],
    ) -> None:
        assert isinstance(dfs_priority, LevelManagerInterface)

    @staticmethod
    def test_starts_in_fallback(
        dfs_priority: DfsPriority[MyProblem],
    ) -> None:
        assert dfs_priority.use_fallback is True

    @staticmethod
    def test_permanent_fallback(
        dfs_priority: DfsPriority[MyProblem],
    ) -> None:
        assert dfs_priority.permanent_fallback is True

    @staticmethod
    def test_dequeue_empty_returns_none(
        dfs_priority: DfsPriority[MyProblem],
    ) -> None:
        assert dfs_priority.dequeue() is None

    @staticmethod
    def test_single_node_round_trip(
        dfs_priority: DfsPriority[MyProblem],
    ) -> None:
        node = _make_node(LB_LOW)
        dfs_priority.enqueue(node)
        assert dfs_priority.dequeue() is node

    @staticmethod
    def test_deepest_level_first() -> None:
        """DfsPriority always dequeues from the deepest non-empty level."""
        q: DfsPriority[MyProblem] = DfsPriority()
        shallow = _make_node(LB_LOW, level=0)
        deep = _make_node(LB_LOW, level=3)
        q.enqueue(shallow)
        q.enqueue(deep)
        assert q.dequeue() is deep

    @staticmethod
    def test_best_first_within_level() -> None:
        """Within the deepest level, the node with the lowest lb is served."""
        q: DfsPriority[MyProblem] = DfsPriority()
        a = _make_node(LB_HIGH, level=2)
        b = _make_node(LB_LOW, level=2)
        q.enqueue(a)
        q.enqueue(b)
        assert q.dequeue() is b

    @staticmethod
    def test_falls_back_to_shallower_when_deep_empty() -> None:
        """Once the deepest level is drained, moves to the next level up."""
        q: DfsPriority[MyProblem] = DfsPriority()
        shallow = _make_node(LB_LOW, level=0)
        deep = _make_node(LB_LOW, level=2)
        q.enqueue(shallow)
        q.enqueue(deep)
        first = q.dequeue()
        assert first is deep
        second = q.dequeue()
        assert second is shallow

    @staticmethod
    def test_never_exits_fallback(
        dfs_priority: DfsPriority[MyProblem],
    ) -> None:
        for i in range(FIVE):
            dfs_priority.enqueue(_make_node(float(i), level=0))
        while dfs_priority.not_empty():
            dfs_priority.dequeue()
        assert dfs_priority.use_fallback is True

    @staticmethod
    def test_nodecount_after_clear(
        dfs_priority: DfsPriority[MyProblem],
    ) -> None:
        """DfsPriority: nodecount is 0 after clear()."""
        nodes = [_make_node(float(i), level=i % TWO) for i in range(FOUR)]
        for n in nodes:
            dfs_priority.enqueue(n)
        assert dfs_priority.nodecount == FOUR
        dfs_priority.clear()
        assert dfs_priority.size() == 0
        assert dfs_priority.nodecount == 0

    @staticmethod
    def test_filter_by_lb(
        dfs_priority: DfsPriority[MyProblem],
    ) -> None:
        dfs_priority.enqueue(_make_node(LB_LOW, level=0))
        dfs_priority.enqueue(_make_node(LB_HIGH, level=1))
        dfs_priority.filter_by_lb(MAX_LB_FILTER)
        assert dfs_priority.size() == 1
        node = dfs_priority.dequeue()
        assert node is not None
        assert node.lb == LB_LOW


# ---------------------------------------------------------------------------
# Integration with BranchAndBound
# ---------------------------------------------------------------------------
@pytest.mark.core
@pytest.mark.levelqueue
class TestIntegration:
    @staticmethod
    def test_build_manager_cbfs() -> None:
        mgr = BranchAndBound.build_manager('cbfs')
        assert isinstance(mgr, CyclicBestSearch)

    @staticmethod
    def test_solve_with_cyclic_best_search() -> None:
        problem = MyProblem(lb_value=LB_MEDIUM, feasible=True)
        bnb = BranchAndBound(problem, manager=CyclicBestSearch())
        result = bnb.solve(maxiter=100)
        assert result.solution.status == OptStatus.OPTIMAL
        assert result.solution.cost == LB_MEDIUM

    @staticmethod
    def test_solve_with_dfs_priority() -> None:
        problem = MyProblem(lb_value=LB_MEDIUM, feasible=True)
        bnb = BranchAndBound(problem, manager=DfsPriority())
        result = bnb.solve(maxiter=100)
        assert result.solution.status == OptStatus.OPTIMAL
        assert result.solution.cost == LB_MEDIUM
