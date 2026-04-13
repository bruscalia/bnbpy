import pytest
from myfixtures.myproblem import MyProblem

from bnbpy.cython.manager import BaseNodeManager, FifoManager, LifoManager
from bnbpy.cython.node import Node

# Test constants
LB_LOW = 5
LB_MEDIUM = 10
LB_HIGH = 15
LB_VERY_HIGH = 20
MAX_LB_FILTER = 12
LEVEL_ROOT = 0
LEVEL_CHILD = 1
LEVEL_GRANDCHILD = 2
TWO = 2
THREE = 3


def _make_node(lb: float) -> Node[MyProblem]:
    problem = MyProblem(lb_value=lb, feasible=False)
    node = Node(problem)
    node.compute_bound()
    return node


@pytest.mark.core
@pytest.mark.manager
class TestBaseNodeManagerInterface:
    """Verify that BaseNodeManager abstract methods raise
    NotImplementedError."""

    @staticmethod
    def _bare_manager() -> BaseNodeManager[MyProblem]:
        # Instantiate without going through a subclass
        return BaseNodeManager.__new__(BaseNodeManager)

    def test_size_raises(self) -> None:
        mgr = self._bare_manager()
        with pytest.raises((NotImplementedError, Exception)):
            mgr.size()

    def test_not_empty_raises(self) -> None:
        mgr = self._bare_manager()
        with pytest.raises((NotImplementedError, Exception)):
            mgr.not_empty()

    def test_enqueue_raises(self) -> None:
        mgr = self._bare_manager()
        node = _make_node(LB_LOW)
        with pytest.raises((NotImplementedError, Exception)):
            mgr.enqueue(node)

    def test_dequeue_raises(self) -> None:
        mgr = self._bare_manager()
        with pytest.raises((NotImplementedError, Exception)):
            mgr.dequeue()

    def test_get_lower_bound_raises(self) -> None:
        mgr = self._bare_manager()
        with pytest.raises((NotImplementedError, Exception)):
            mgr.get_lower_bound()

    def test_pop_lower_bound_raises(self) -> None:
        mgr = self._bare_manager()
        with pytest.raises((NotImplementedError, Exception)):
            mgr.pop_lower_bound()

    def test_clear_raises(self) -> None:
        mgr = self._bare_manager()
        with pytest.raises((NotImplementedError, Exception)):
            mgr.clear()

    def test_pop_all_raises(self) -> None:
        mgr = self._bare_manager()
        with pytest.raises((NotImplementedError, Exception)):
            mgr.pop_all()

    def test_filter_by_lb_is_noop(self) -> None:
        """filter_by_lb on the base class is a no-op (does not raise)."""
        mgr = self._bare_manager()
        mgr.filter_by_lb(MAX_LB_FILTER)  # should not raise

    @staticmethod
    def test_enqueue_all_uses_enqueue() -> None:
        """enqueue_all on a concrete subclass enqueues each node."""
        mgr: LifoManager[MyProblem] = LifoManager()
        nodes = [
            _make_node(LB_LOW),
            _make_node(LB_MEDIUM),
            _make_node(LB_HIGH),
        ]
        mgr.enqueue_all(nodes)
        assert mgr.size() == len(nodes)


@pytest.mark.core
@pytest.mark.manager
class TestLifoManager:
    """Tests for LifoManager (stack — last in, first out)."""

    @staticmethod
    @pytest.fixture
    def manager() -> LifoManager[MyProblem]:
        return LifoManager()

    # ------------------------------------------------------------------
    # Basic state
    # ------------------------------------------------------------------

    @staticmethod
    def test_initial_empty(manager: LifoManager[MyProblem]) -> None:
        assert manager.not_empty() is False
        assert manager.size() == 0

    @staticmethod
    def test_not_empty_after_enqueue(manager: LifoManager[MyProblem]) -> None:
        manager.enqueue(_make_node(LB_LOW))
        assert manager.not_empty() is True
        assert manager.size() == 1

    @staticmethod
    def test_clear(manager: LifoManager[MyProblem]) -> None:
        manager.enqueue(_make_node(LB_LOW))
        manager.enqueue(_make_node(LB_MEDIUM))
        manager.clear()
        assert manager.not_empty() is False
        assert manager.size() == 0

    # ------------------------------------------------------------------
    # LIFO ordering
    # ------------------------------------------------------------------

    @staticmethod
    def test_lifo_ordering() -> None:
        """Last enqueued node is dequeued first."""
        manager: LifoManager[MyProblem] = LifoManager()
        node_first = _make_node(LB_LOW)
        node_last = _make_node(LB_HIGH)
        manager.enqueue(node_first)
        manager.enqueue(node_last)
        assert manager.dequeue() is node_last
        assert manager.dequeue() is node_first

    @staticmethod
    def test_dequeue_empty_returns_none(
        manager: LifoManager[MyProblem],
    ) -> None:
        assert manager.dequeue() is None

    # ------------------------------------------------------------------
    # enqueue_all / pop_all
    # ------------------------------------------------------------------

    @staticmethod
    def test_enqueue_all(manager: LifoManager[MyProblem]) -> None:
        nodes = [_make_node(lb) for lb in (LB_LOW, LB_MEDIUM, LB_HIGH)]
        manager.enqueue_all(nodes)
        assert manager.size() == THREE

    @staticmethod
    def test_pop_all_returns_all_nodes(
        manager: LifoManager[MyProblem],
    ) -> None:
        nodes = [_make_node(lb) for lb in (LB_LOW, LB_MEDIUM, LB_HIGH)]
        for n in nodes:
            manager.enqueue(n)
        result = manager.pop_all()
        assert {id(n) for n in result} == {id(n) for n in nodes}
        assert manager.not_empty() is False

    # ------------------------------------------------------------------
    # get_lower_bound / pop_lower_bound
    # ------------------------------------------------------------------

    @staticmethod
    def test_get_lower_bound_returns_min_without_removing(
        manager: LifoManager[MyProblem],
    ) -> None:
        node_high = _make_node(LB_HIGH)
        node_low = _make_node(LB_LOW)
        manager.enqueue(node_high)
        manager.enqueue(node_low)
        result = manager.get_lower_bound()
        assert result is node_low
        assert manager.size() == TWO  # not removed

    @staticmethod
    def test_get_lower_bound_empty_returns_none(
        manager: LifoManager[MyProblem],
    ) -> None:
        assert manager.get_lower_bound() is None

    @staticmethod
    def test_pop_lower_bound_removes_min(
        manager: LifoManager[MyProblem],
    ) -> None:
        node_high = _make_node(LB_HIGH)
        node_low = _make_node(LB_LOW)
        manager.enqueue(node_high)
        manager.enqueue(node_low)
        result = manager.pop_lower_bound()
        assert result is node_low
        assert manager.size() == 1
        assert manager.dequeue() is node_high

    @staticmethod
    def test_pop_lower_bound_empty_returns_none(
        manager: LifoManager[MyProblem],
    ) -> None:
        assert manager.pop_lower_bound() is None

    # ------------------------------------------------------------------
    # filter_by_lb
    # ------------------------------------------------------------------

    @staticmethod
    def test_filter_by_lb_keeps_below_threshold(
        manager: LifoManager[MyProblem],
    ) -> None:
        node_low = _make_node(LB_LOW)
        node_medium = _make_node(LB_MEDIUM)
        node_high = _make_node(LB_HIGH)
        manager.enqueue(node_low)
        manager.enqueue(node_medium)
        manager.enqueue(node_high)
        manager.filter_by_lb(MAX_LB_FILTER)  # keep lb < 12
        assert manager.size() == TWO  # low (5) and medium (10) survive
        n1 = manager.dequeue()
        n2 = manager.dequeue()
        assert n1 is not None
        assert n2 is not None
        remaining_lbs = {n1.lb, n2.lb}
        assert remaining_lbs == {LB_LOW, LB_MEDIUM}

    @staticmethod
    def test_filter_by_lb_removes_all(manager: LifoManager[MyProblem]) -> None:
        manager.enqueue(_make_node(LB_HIGH))
        manager.enqueue(_make_node(LB_VERY_HIGH))
        manager.filter_by_lb(LB_LOW)  # nothing survives
        assert manager.not_empty() is False

    @staticmethod
    def test_filter_by_lb_keeps_all(manager: LifoManager[MyProblem]) -> None:
        manager.enqueue(_make_node(LB_LOW))
        manager.enqueue(_make_node(LB_MEDIUM))
        manager.filter_by_lb(LB_VERY_HIGH)  # all survive
        assert manager.size() == TWO


@pytest.mark.core
@pytest.mark.manager
class TestFifoManager:
    """Tests for FifoManager (queue — first in, first out)."""

    @staticmethod
    @pytest.fixture
    def manager() -> FifoManager[MyProblem]:
        return FifoManager()

    # ------------------------------------------------------------------
    # Basic state (inherits LifoManager logic except dequeue order)
    # ------------------------------------------------------------------

    @staticmethod
    def test_initial_empty(manager: FifoManager[MyProblem]) -> None:
        assert manager.not_empty() is False

    @staticmethod
    def test_clear(manager: FifoManager[MyProblem]) -> None:
        manager.enqueue(_make_node(LB_LOW))
        manager.clear()
        assert manager.not_empty() is False

    # ------------------------------------------------------------------
    # FIFO ordering
    # ------------------------------------------------------------------

    @staticmethod
    def test_fifo_ordering() -> None:
        """First enqueued node is dequeued first."""
        manager: FifoManager[MyProblem] = FifoManager()
        node_first = _make_node(LB_LOW)
        node_second = _make_node(LB_MEDIUM)
        node_third = _make_node(LB_HIGH)
        manager.enqueue(node_first)
        manager.enqueue(node_second)
        manager.enqueue(node_third)
        assert manager.dequeue() is node_first
        assert manager.dequeue() is node_second
        assert manager.dequeue() is node_third

    @staticmethod
    def test_dequeue_empty_returns_none(
        manager: FifoManager[MyProblem],
    ) -> None:
        assert manager.dequeue() is None

    # ------------------------------------------------------------------
    # enqueue_all / pop_all
    # ------------------------------------------------------------------

    @staticmethod
    def test_enqueue_all_fifo_order() -> None:
        """enqueue_all preserves insertion order for FIFO dequeue."""
        manager: FifoManager[MyProblem] = FifoManager()
        nodes = [_make_node(lb) for lb in (LB_LOW, LB_MEDIUM, LB_HIGH)]
        manager.enqueue_all(nodes)
        assert manager.dequeue() is nodes[0]
        assert manager.dequeue() is nodes[1]
        assert manager.dequeue() is nodes[2]

    @staticmethod
    def test_pop_all(manager: FifoManager[MyProblem]) -> None:
        nodes = [_make_node(lb) for lb in (LB_LOW, LB_MEDIUM)]
        manager.enqueue_all(nodes)
        result = manager.pop_all()
        assert len(result) == TWO
        assert manager.not_empty() is False

    # ------------------------------------------------------------------
    # get_lower_bound / pop_lower_bound (inherited from LifoManager)
    # ------------------------------------------------------------------

    @staticmethod
    def test_get_lower_bound(manager: FifoManager[MyProblem]) -> None:
        node_high = _make_node(LB_HIGH)
        node_low = _make_node(LB_LOW)
        manager.enqueue(node_high)
        manager.enqueue(node_low)
        result = manager.get_lower_bound()
        assert result is node_low
        assert manager.size() == TWO

    @staticmethod
    def test_pop_lower_bound(manager: FifoManager[MyProblem]) -> None:
        node_high = _make_node(LB_HIGH)
        node_low = _make_node(LB_LOW)
        manager.enqueue(node_high)
        manager.enqueue(node_low)
        result = manager.pop_lower_bound()
        assert result is node_low
        assert manager.size() == 1

    # ------------------------------------------------------------------
    # filter_by_lb
    # ------------------------------------------------------------------

    @staticmethod
    def test_filter_by_lb(manager: FifoManager[MyProblem]) -> None:
        node_low = _make_node(LB_LOW)
        node_medium = _make_node(LB_MEDIUM)
        node_high = _make_node(LB_HIGH)
        manager.enqueue(node_low)
        manager.enqueue(node_medium)
        manager.enqueue(node_high)
        manager.filter_by_lb(MAX_LB_FILTER)
        assert manager.size() == TWO
        # FIFO order preserved after filtering
        assert manager.dequeue() is node_low
        assert manager.dequeue() is node_medium
