import pytest
from myfixtures.myproblem import MyProblem

from bnbpy.cython.cbfs import CycleLevel, CycleQueue
from bnbpy.cython.node import Node
from bnbpy.cython.priqueue import DfsPriQueue
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


# ---------------------------------------------------------------------------
# Helpers
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
def queue() -> CycleQueue[MyProblem]:
    return CycleQueue()


@pytest.fixture
def small_queue() -> CycleQueue[MyProblem]:
    """A CycleQueue with a very low max_size for fallback testing."""
    return CycleQueue(max_size=FIVE)


# ---------------------------------------------------------------------------
# CycleLevel
# ---------------------------------------------------------------------------
@pytest.mark.core
@pytest.mark.cbfs
class TestCycleLevel:
    """Tests for CycleLevel — the per-depth bucket inside CycleQueue."""

    @staticmethod
    def test_initial_state() -> None:
        level: CycleLevel[MyProblem] = CycleLevel(0)
        assert level.level == 0
        assert level.size() == 0

    @staticmethod
    def test_self_linked() -> None:
        """A freshly created level links to itself."""
        level: CycleLevel[MyProblem] = CycleLevel(0)
        assert level.next is level
        assert level.prev is level

    @staticmethod
    def test_add_and_pop_node() -> None:
        level: CycleLevel[MyProblem] = CycleLevel(0)
        node = _make_node(LB_LOW)
        level.add_node(node)
        assert level.size() == 1
        popped = level.pop_node()
        assert popped is node
        assert level.size() == 0

    @staticmethod
    def test_pop_empty_returns_none() -> None:
        level: CycleLevel[MyProblem] = CycleLevel(0)
        assert level.pop_node() is None

    @staticmethod
    def test_best_first_ordering() -> None:
        """CycleLevel uses BestPriQueue by default — lowest lb first."""
        level: CycleLevel[MyProblem] = CycleLevel(0)
        high = _make_node(LB_HIGH)
        low = _make_node(LB_LOW)
        level.add_node(high)
        level.add_node(low)
        assert level.pop_node() is low
        assert level.pop_node() is high

    @staticmethod
    def test_set_queue_replaces_inner() -> None:
        level: CycleLevel[MyProblem] = CycleLevel(0)
        node = _make_node(LB_LOW)
        level.add_node(node)
        # Replace with a fresh queue — old node is gone
        level.set_queue(DfsPriQueue())
        assert level.size() == 0

    @staticmethod
    def test_filter_removes_above_threshold() -> None:
        level: CycleLevel[MyProblem] = CycleLevel(0)
        level.add_node(_make_node(LB_LOW))
        level.add_node(_make_node(LB_HIGH))
        level.filter(MAX_LB_FILTER)  # keep lb < 12
        assert level.size() == 1
        result = level.pop_node()
        assert result is not None
        assert result.lb == LB_LOW

    @staticmethod
    def test_class_getitem() -> None:
        """CycleLevel[MyProblem] returns CycleLevel itself."""
        assert CycleLevel[MyProblem] is CycleLevel


# ---------------------------------------------------------------------------
# CycleQueue — basic state
# ---------------------------------------------------------------------------
@pytest.mark.core
@pytest.mark.cbfs
class TestCycleQueueBasic:
    """Initialisation, size, not_empty, clear."""

    @staticmethod
    def test_initial_state(queue: CycleQueue[MyProblem]) -> None:
        assert queue.not_empty() is False
        assert queue.size() == 0

    @staticmethod
    def test_not_empty_after_enqueue(
        queue: CycleQueue[MyProblem],
    ) -> None:
        queue.enqueue(_make_node(LB_LOW))
        assert queue.not_empty() is True
        assert queue.size() == 1

    @staticmethod
    def test_clear(queue: CycleQueue[MyProblem]) -> None:
        queue.enqueue(_make_node(LB_LOW))
        queue.enqueue(_make_node(LB_MEDIUM, level=1))
        queue.clear()
        assert queue.not_empty() is False
        assert queue.size() == 0


# ---------------------------------------------------------------------------
# CycleQueue — enqueue / dequeue
# ---------------------------------------------------------------------------
@pytest.mark.core
@pytest.mark.cbfs
class TestCycleQueueEnqueueDequeue:
    """Enqueue and dequeue semantics including round-robin cycling."""

    @staticmethod
    def test_dequeue_empty_returns_none(
        queue: CycleQueue[MyProblem],
    ) -> None:
        assert queue.dequeue() is None

    @staticmethod
    def test_single_node_round_trip(
        queue: CycleQueue[MyProblem],
    ) -> None:
        node = _make_node(LB_LOW)
        queue.enqueue(node)
        assert queue.dequeue() is node
        assert queue.not_empty() is False

    @staticmethod
    def test_same_level_best_first(
        queue: CycleQueue[MyProblem],
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
        queue: CycleQueue[MyProblem],
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

        # Level 0 best, then level 1 best, then level 0 next, ...
        first = queue.dequeue()
        second = queue.dequeue()
        third = queue.dequeue()
        fourth = queue.dequeue()

        assert first is n0a  # level 0 best
        assert second is n1a  # level 1 best
        assert third is n0b  # level 0 next
        assert fourth is n1b  # level 1 next

    @staticmethod
    def test_skips_empty_levels(
        queue: CycleQueue[MyProblem],
    ) -> None:
        """Dequeue skips levels with no remaining nodes."""
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
        queue: CycleQueue[MyProblem],
    ) -> None:
        """Enqueueing a node at a deep level creates intermediate levels."""
        deep = _make_node(LB_LOW, level=5)
        queue.enqueue(deep)
        n_levels = 6  # levels 0..5
        assert len(queue.levels) == n_levels
        assert queue.dequeue() is deep


# ---------------------------------------------------------------------------
# CycleQueue — get_lower_bound
# ---------------------------------------------------------------------------
@pytest.mark.core
@pytest.mark.cbfs
class TestCycleQueueLowerBound:
    """Tests for get_lower_bound (peek) across levels."""

    @staticmethod
    def test_empty_returns_none(queue: CycleQueue[MyProblem]) -> None:
        assert queue.get_lower_bound() is None

    @staticmethod
    def test_returns_global_minimum(
        queue: CycleQueue[MyProblem],
    ) -> None:
        high = _make_node(LB_HIGH, level=0)
        low = _make_node(LB_LOW, level=1)
        med = _make_node(LB_MEDIUM, level=2)
        queue.enqueue(high)
        queue.enqueue(low)
        queue.enqueue(med)
        result = queue.get_lower_bound()
        assert result is low
        # Node is not removed — size unchanged
        assert queue.size() == THREE

    @staticmethod
    def test_pop_lower_bound_raises(
        queue: CycleQueue[MyProblem],
    ) -> None:
        """CycleQueue does not implement pop_lower_bound."""
        queue.enqueue(_make_node(LB_LOW))
        with pytest.raises(NotImplementedError):
            queue.pop_lower_bound()

    @staticmethod
    def test_pop_all_raises(
        queue: CycleQueue[MyProblem],
    ) -> None:
        """CycleQueue does not implement pop_all."""
        queue.enqueue(_make_node(LB_LOW))
        with pytest.raises(NotImplementedError):
            queue.pop_all()


# ---------------------------------------------------------------------------
# CycleQueue — filter_by_lb
# ---------------------------------------------------------------------------
@pytest.mark.core
@pytest.mark.cbfs
class TestCycleQueueFilter:
    """Tests for filter_by_lb across levels."""

    @staticmethod
    def test_filter_keeps_below(queue: CycleQueue[MyProblem]) -> None:
        queue.enqueue(_make_node(LB_LOW, level=0))
        queue.enqueue(_make_node(LB_MEDIUM, level=1))
        queue.enqueue(_make_node(LB_HIGH, level=2))
        queue.filter_by_lb(MAX_LB_FILTER)  # keep lb < 12
        assert queue.size() == TWO

    @staticmethod
    def test_filter_removes_all(queue: CycleQueue[MyProblem]) -> None:
        queue.enqueue(_make_node(LB_HIGH, level=0))
        queue.enqueue(_make_node(LB_VERY_HIGH, level=1))
        queue.filter_by_lb(LB_LOW)
        assert queue.not_empty() is False
        assert queue.size() == 0

    @staticmethod
    def test_filter_keeps_all(queue: CycleQueue[MyProblem]) -> None:
        queue.enqueue(_make_node(LB_LOW, level=0))
        queue.enqueue(_make_node(LB_MEDIUM, level=1))
        queue.filter_by_lb(LB_VERY_HIGH)
        assert queue.size() == TWO


# ---------------------------------------------------------------------------
# CycleQueue — reset_level
# ---------------------------------------------------------------------------
@pytest.mark.core
@pytest.mark.cbfs
class TestCycleQueueResetLevel:
    """Tests for reset_level (rewind current pointer to start)."""

    @staticmethod
    def test_reset_rewinds_cycle(queue: CycleQueue[MyProblem]) -> None:
        """After a partial cycle, reset_level restarts from level 0."""
        n0 = _make_node(LB_LOW, level=0)
        n1 = _make_node(LB_LOW, level=1)
        n0b = _make_node(LB_MEDIUM, level=0)
        queue.enqueue(n0)
        queue.enqueue(n1)
        queue.enqueue(n0b)

        # Dequeue from level 0, advancing pointer to level 1
        first = queue.dequeue()
        assert first is n0

        # Reset — next dequeue should come from level 0 again
        queue.reset_level()
        second = queue.dequeue()
        assert second is n0b


# ---------------------------------------------------------------------------
# CycleQueue — fallback mode
# ---------------------------------------------------------------------------
@pytest.mark.core
@pytest.mark.cbfs
class TestCycleQueueFallback:
    """Tests for the DFS fallback triggered by max_size overflow."""

    @staticmethod
    def test_enters_fallback_on_overflow(
        small_queue: CycleQueue[MyProblem],
    ) -> None:
        """After exceeding max_size, use_fallback becomes True."""
        for i in range(FIVE + TWO):
            small_queue.enqueue(_make_node(float(i), level=0))
        assert small_queue.use_fallback is True

    @staticmethod
    def test_dequeue_in_fallback(
        small_queue: CycleQueue[MyProblem],
    ) -> None:
        """Nodes can still be dequeued while in fallback mode."""
        nodes = [_make_node(float(i), level=0) for i in range(FIVE + TWO)]
        for n in nodes:
            small_queue.enqueue(n)
        assert small_queue.use_fallback is True
        # Dequeue works and returns a node
        node = small_queue.dequeue()
        assert node is not None

    @staticmethod
    def test_exits_fallback_after_drain(
        small_queue: CycleQueue[MyProblem],
    ) -> None:
        """Draining below max_size // 2 exits fallback mode."""
        for i in range(FIVE + TWO):
            small_queue.enqueue(_make_node(float(i), level=0))
        assert small_queue.use_fallback is True

        # Drain until at most max_size // 2
        while small_queue.size() > small_queue.max_size // 2:
            small_queue.dequeue()
        # One more dequeue triggers exit check
        small_queue.dequeue()
        assert small_queue.use_fallback is False

    @staticmethod
    def test_fallback_filter_updates_count(
        small_queue: CycleQueue[MyProblem],
    ) -> None:
        """filter_by_lb works across both level queues and fallback."""
        for i in range(FIVE + TWO):
            small_queue.enqueue(_make_node(float(i) * 5, level=0))
        # All nodes in fallback now; filter keeps only lb < 12
        small_queue.filter_by_lb(MAX_LB_FILTER)
        for _ in range(small_queue.size()):
            node = small_queue.dequeue()
            assert node is not None
            assert node.lb < MAX_LB_FILTER

    @staticmethod
    def test_enqueue_during_fallback_uses_fallback(
        small_queue: CycleQueue[MyProblem],
    ) -> None:
        """Nodes enqueued while in fallback go to the fallback queue."""
        for i in range(FIVE + TWO):
            small_queue.enqueue(_make_node(float(i), level=0))
        assert small_queue.use_fallback is True
        before = small_queue.size()
        small_queue.enqueue(_make_node(LB_LOW, level=0))
        assert small_queue.size() == before + 1

    @staticmethod
    def test_get_lower_bound_checks_fallback(
        small_queue: CycleQueue[MyProblem],
    ) -> None:
        """get_lower_bound considers nodes in the fallback queue."""
        low = _make_node(LB_LOW, level=0)
        for _ in range(FIVE):
            small_queue.enqueue(_make_node(LB_HIGH, level=0))
        small_queue.enqueue(low)  # triggers fallback
        result = small_queue.get_lower_bound()
        assert result is not None
        assert result.lb == LB_LOW


# ---------------------------------------------------------------------------
# CycleQueue — new_level factory
# ---------------------------------------------------------------------------
@pytest.mark.core
@pytest.mark.cbfs
class TestCycleQueueNewLevel:
    """Tests for the new_level factory method."""

    @staticmethod
    def test_new_level_creates_cycle_level(
        queue: CycleQueue[MyProblem],
    ) -> None:
        lvl = queue.new_level(NEW_LEVEL)
        assert isinstance(lvl, CycleLevel)
        assert lvl.level == NEW_LEVEL

    @staticmethod
    def test_new_level_has_empty_queue(
        queue: CycleQueue[MyProblem],
    ) -> None:
        lvl = queue.new_level(0)
        assert lvl.size() == 0


# ---------------------------------------------------------------------------
# CycleQueue — integration with BranchAndBound
# ---------------------------------------------------------------------------
@pytest.mark.core
@pytest.mark.cbfs
class TestCycleQueueIntegration:
    """Verify CycleQueue works end-to-end with BranchAndBound."""

    @staticmethod
    def test_build_manager_cbfs() -> None:
        mgr = BranchAndBound.build_manager('cbfs')
        assert isinstance(mgr, CycleQueue)

    @staticmethod
    def test_solve_with_cbfs_manager() -> None:
        problem = MyProblem(lb_value=LB_MEDIUM, feasible=True)
        bnb = BranchAndBound(problem, manager=CycleQueue())
        result = bnb.solve(maxiter=100)
        assert result.solution.status == OptStatus.OPTIMAL
        assert result.solution.cost == LB_MEDIUM
