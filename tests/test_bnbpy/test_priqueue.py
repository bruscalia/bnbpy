import pytest
from myfixtures.myproblem import MyProblem

from bnbpy.cython.node import Node
from bnbpy.cython.primanager import (
    BestFirstSearch,
    DepthFirstSearch,
    PriorityManagerTemplate,
)

# Test constants
LB_LOW = 5
LB_MEDIUM = 10
LB_HIGH = 15
LB_VERY_HIGH = 20
MAX_LB_FILTER = 12
LEVEL_ROOT = 0
LEVEL_CHILD = 1
LEVEL_GRANDCHILD = 2
LEVEL_DEEP = 3


@pytest.mark.core
@pytest.mark.priqueue
class TestPriorityManagerTemplate:
    """Tests for PriorityManagerTemplate using DepthFirstSearch."""

    @staticmethod
    @pytest.fixture
    def empty_queue() -> DepthFirstSearch[MyProblem]:
        """Use DepthFirstSearch as concrete implementation."""
        return DepthFirstSearch()

    @staticmethod
    @pytest.fixture
    def node_low() -> Node[MyProblem]:
        problem = MyProblem(lb_value=LB_LOW, feasible=False)
        node = Node(problem)
        node.compute_bound()
        return node

    @staticmethod
    @pytest.fixture
    def node_medium() -> Node[MyProblem]:
        problem = MyProblem(lb_value=LB_MEDIUM, feasible=False)
        node = Node(problem)
        node.compute_bound()
        return node

    @staticmethod
    @pytest.fixture
    def node_high() -> Node[MyProblem]:
        problem = MyProblem(lb_value=LB_HIGH, feasible=False)
        node = Node(problem)
        node.compute_bound()
        return node

    @staticmethod
    def test_initialization(empty_queue: DepthFirstSearch[MyProblem]) -> None:
        assert empty_queue.not_empty() is False

    @staticmethod
    def test_not_empty_after_enqueue(
        empty_queue: DepthFirstSearch[MyProblem], node_low: Node[MyProblem]
    ) -> None:
        """Test that not_empty returns True after enqueueing a node."""
        empty_queue.enqueue(node_low)
        assert empty_queue.not_empty() is True

    @staticmethod
    def test_dequeue_empty_queue(
        empty_queue: DepthFirstSearch[MyProblem],
    ) -> None:
        """Test that dequeue returns None for an empty queue."""
        result = empty_queue.dequeue()
        assert result is None

    @staticmethod
    def test_get_lower_bound_empty_queue(
        empty_queue: DepthFirstSearch[MyProblem],
    ) -> None:
        """Test that get_lower_bound returns None for an empty queue."""
        result = empty_queue.get_lower_bound()
        assert result is None

    @staticmethod
    def test_get_lower_bound_single_node(
        empty_queue: DepthFirstSearch[MyProblem], node_low: Node[MyProblem]
    ) -> None:
        """Test get_lower_bound with a single node."""
        empty_queue.enqueue(node_low)
        result = empty_queue.get_lower_bound()
        assert result is node_low
        assert result.lb == LB_LOW

    @staticmethod
    def test_get_lower_bound_multiple_nodes(
        empty_queue: DepthFirstSearch[MyProblem],
        node_low: Node[MyProblem],
        node_medium: Node[MyProblem],
        node_high: Node[MyProblem],
    ) -> None:
        """Test get_lower_bound returns node with lowest lb."""
        empty_queue.enqueue(node_high)
        empty_queue.enqueue(node_low)
        empty_queue.enqueue(node_medium)
        result = empty_queue.get_lower_bound()
        assert result is node_low
        assert result.lb == LB_LOW

    @staticmethod
    def test_clear(
        empty_queue: DepthFirstSearch[MyProblem],
        node_low: Node[MyProblem],
        node_medium: Node[MyProblem],
    ) -> None:
        """Test that clear empties the queue."""
        empty_queue.enqueue(node_low)
        empty_queue.enqueue(node_medium)
        assert empty_queue.not_empty() is True
        empty_queue.clear()
        assert empty_queue.not_empty() is False

    @staticmethod
    def test_filter_by_lb(
        empty_queue: DepthFirstSearch[MyProblem],
        node_low: Node[MyProblem],
        node_medium: Node[MyProblem],
        node_high: Node[MyProblem],
    ) -> None:
        """Test that filter_by_lb removes nodes with lb >= max_lb."""
        empty_queue.enqueue(node_low)
        empty_queue.enqueue(node_medium)
        empty_queue.enqueue(node_high)
        # Filter: keep only nodes with lb < 12
        empty_queue.filter_by_lb(MAX_LB_FILTER)
        # Should keep node_low (5) and node_medium (10)
        # Should remove node_high (15)
        assert empty_queue.not_empty() is True
        first = empty_queue.dequeue()
        second = empty_queue.dequeue()
        third = empty_queue.dequeue()
        assert first is not None
        assert first.lb == LB_LOW
        assert second is not None
        assert second.lb == LB_MEDIUM
        assert third is None

    @staticmethod
    def test_make_priority_raises() -> None:
        """PriorityManagerTemplate.make_priority raises NotImplementedError."""
        queue: PriorityManagerTemplate[MyProblem] = PriorityManagerTemplate()
        node = Node(MyProblem(lb_value=LB_LOW, feasible=False))
        node.compute_bound()
        with pytest.raises(NotImplementedError):
            queue.make_priority(node)


@pytest.mark.core
@pytest.mark.priqueue
class TestDepthFirstSearch:
    """Test class for DepthFirstSearch (Depth-First Search) functionality."""

    @staticmethod
    @pytest.fixture
    def dfs_queue() -> DepthFirstSearch[MyProblem]:
        return DepthFirstSearch()

    @staticmethod
    def test_initialization(dfs_queue: DepthFirstSearch[MyProblem]) -> None:
        """Test the initialization of a DepthFirstSearch instance."""
        assert dfs_queue.not_empty() is False

    @staticmethod
    def test_dfs_ordering() -> None:
        """Test that DFS queue dequeues deeper nodes first."""
        queue: DepthFirstSearch[MyProblem] = DepthFirstSearch()
        # Create nodes at different levels
        root_problem = MyProblem(lb_value=LB_LOW, feasible=False)
        root = Node(root_problem)
        root.compute_bound()
        root.level = LEVEL_ROOT

        child_problem = MyProblem(lb_value=LB_MEDIUM, feasible=False)
        child = Node(child_problem)
        child.compute_bound()
        child.level = LEVEL_CHILD
        child.parent = root

        grandchild_problem = MyProblem(lb_value=LB_HIGH, feasible=False)
        grandchild = Node(grandchild_problem)
        grandchild.compute_bound()
        grandchild.level = LEVEL_GRANDCHILD
        grandchild.parent = child

        # Enqueue in non-DFS order
        queue.enqueue(root)
        queue.enqueue(child)
        queue.enqueue(grandchild)

        # DFS should dequeue deepest first (highest level)
        first = queue.dequeue()
        second = queue.dequeue()
        third = queue.dequeue()

        assert first is not None
        assert first.level == LEVEL_GRANDCHILD  # grandchild
        assert second is not None
        assert second.level == LEVEL_CHILD  # child
        assert third is not None
        assert third.level == LEVEL_ROOT  # root

    @staticmethod
    def test_dfs_same_level_ordering() -> None:
        """Test DFS ordering when nodes are at the same level."""
        queue: DepthFirstSearch[MyProblem] = DepthFirstSearch()
        # Create nodes at the same level with different bounds
        problem1 = MyProblem(lb_value=LB_HIGH, feasible=False)
        node1 = Node(problem1)
        node1.compute_bound()
        node1.level = LEVEL_CHILD

        problem2 = MyProblem(lb_value=LB_LOW, feasible=False)
        node2 = Node(problem2)
        node2.compute_bound()
        node2.level = LEVEL_CHILD

        queue.enqueue(node1)
        queue.enqueue(node2)

        # At same level, should use lb as tiebreaker (lower lb first)
        first = queue.dequeue()
        second = queue.dequeue()

        assert first is not None
        assert first.lb == LB_LOW
        assert second is not None
        assert second.lb == LB_HIGH


@pytest.mark.core
@pytest.mark.priqueue
class TestBestFirstSearch:
    """Test class for BestFirstSearch (Best-First Search) functionality."""

    @staticmethod
    @pytest.fixture
    def best_queue() -> BestFirstSearch[MyProblem]:
        return BestFirstSearch()

    @staticmethod
    def test_initialization(best_queue: BestFirstSearch[MyProblem]) -> None:
        """Test the initialization of a BestFirstSearch instance."""
        assert best_queue.not_empty() is False

    @staticmethod
    def test_best_first_ordering() -> None:
        """Test that best-first queue dequeues nodes with lowest lb."""
        queue: BestFirstSearch[MyProblem] = BestFirstSearch()
        # Create nodes with different bounds and levels
        problem_high = MyProblem(lb_value=LB_HIGH, feasible=False)
        node_high = Node(problem_high)
        node_high.compute_bound()
        node_high.level = LEVEL_ROOT

        problem_low = MyProblem(lb_value=LB_LOW, feasible=False)
        node_low = Node(problem_low)
        node_low.compute_bound()
        node_low.level = LEVEL_GRANDCHILD

        problem_medium = MyProblem(lb_value=LB_MEDIUM, feasible=False)
        node_medium = Node(problem_medium)
        node_medium.compute_bound()
        node_medium.level = LEVEL_CHILD

        # Enqueue in random order
        queue.enqueue(node_high)
        queue.enqueue(node_low)
        queue.enqueue(node_medium)

        # Best-first should dequeue by lowest lb first
        first = queue.dequeue()
        second = queue.dequeue()
        third = queue.dequeue()

        assert first is not None
        assert first.lb == LB_LOW
        assert second is not None
        assert second.lb == LB_MEDIUM
        assert third is not None
        assert third.lb == LB_HIGH

    @staticmethod
    def test_best_first_same_lb_ordering() -> None:
        """Test best-first ordering when nodes have the same lb.

        When lb values are equal BestFirstSearch breaks ties by level depth
        (deeper nodes first), then by insertion index.
        """
        queue: BestFirstSearch[MyProblem] = BestFirstSearch()
        # Create nodes with same lb but different levels
        problem1 = MyProblem(lb_value=LB_LOW, feasible=False)
        node1 = Node(problem1)
        node1.compute_bound()
        node1.level = LEVEL_CHILD

        problem2 = MyProblem(lb_value=LB_LOW, feasible=False)
        node2 = Node(problem2)
        node2.compute_bound()
        node2.level = LEVEL_DEEP

        queue.enqueue(node1)
        queue.enqueue(node2)

        # Both have the same lb — both should be returned with LB_LOW
        first = queue.dequeue()
        second = queue.dequeue()

        assert first is not None
        assert first.lb == LB_LOW
        assert second is not None
        assert second.lb == LB_LOW

    @staticmethod
    def test_best_first_mixed_scenario() -> None:
        """Test best-first with mixed bounds and levels.

        BestFirstSearch orders by lb first, then by level depth (deeper first),
        then by insertion index.
        """
        queue: BestFirstSearch[MyProblem] = BestFirstSearch()
        # Create a realistic scenario
        nodes = []
        bounds = [LB_HIGH, LB_LOW, LB_MEDIUM, LB_VERY_HIGH, LB_LOW]
        levels = [
            LEVEL_ROOT,
            LEVEL_GRANDCHILD,
            LEVEL_CHILD,
            LEVEL_ROOT,
            LEVEL_DEEP,
        ]

        for lb, level in zip(bounds, levels):
            problem = MyProblem(lb_value=lb, feasible=False)
            node = Node(problem)
            node.compute_bound()
            node.level = level
            nodes.append(node)
            queue.enqueue(node)

        # Should dequeue in lb order: two LB_LOW, then LB_MEDIUM, LB_HIGH,
        # LB_VERY_HIGH.  Order within the same lb is unspecified.
        first = queue.dequeue()
        assert first is not None
        assert first.lb == LB_LOW

        second = queue.dequeue()
        assert second is not None
        assert second.lb == LB_LOW

        third = queue.dequeue()
        assert third is not None
        assert third.lb == LB_MEDIUM

        fourth = queue.dequeue()
        assert fourth is not None
        assert fourth.lb == LB_HIGH

        fifth = queue.dequeue()
        assert fifth is not None
        assert fifth.lb == LB_VERY_HIGH


@pytest.mark.core
@pytest.mark.priqueue
class TestBoundNodesTracking:
    """Tests for the bound_nodes bookkeeping in PriorityQueue.

    These cases guard against a regression where enqueueing a node with a
    strictly lower lb failed to clear stale entries from bound_nodes.

    Root cause: the old enqueue() updated self.lb *before* calling
    enqueue_bound_update, so the inner check ``node.lb < self.lb`` was
    never True and bound_nodes was never cleared.  get_lower_bound() then
    short-circuited on the stale set and returned a higher-lb node.
    """

    @staticmethod
    def test_bound_nodes_cleared_when_lower_lb_enqueued() -> None:
        """Enqueueing a node with strictly lower lb replaces bound_nodes.

        After enqueue(high) then enqueue(low), get_lower_bound() must return
        the low node, not the high one that was first added to bound_nodes.
        """
        queue: BestFirstSearch[MyProblem] = BestFirstSearch()
        node_high = Node(MyProblem(lb_value=LB_HIGH, feasible=False))
        node_high.compute_bound()
        node_low = Node(MyProblem(lb_value=LB_LOW, feasible=False))
        node_low.compute_bound()

        queue.enqueue(node_high)  # bound_nodes <- {node_high}, lb = LB_HIGH
        queue.enqueue(node_low)  # must clear {node_high}, lb = LB_LOW

        # get_lower_bound uses the bound_nodes short-circuit — must return
        # node_low, not node_high
        result = queue.get_lower_bound()
        assert result is node_low

        # Drain: first out must still be the lowest-lb node
        first = queue.dequeue()
        assert first is node_low

    @staticmethod
    def test_bound_nodes_not_stale_across_multiple_lb_drops() -> None:
        """bound_nodes is replaced, not accumulated, on each lb drop."""
        queue: BestFirstSearch[MyProblem] = BestFirstSearch()
        node_a = Node(MyProblem(lb_value=LB_VERY_HIGH, feasible=False))
        node_a.compute_bound()
        node_b = Node(MyProblem(lb_value=LB_HIGH, feasible=False))
        node_b.compute_bound()
        node_c = Node(MyProblem(lb_value=LB_MEDIUM, feasible=False))
        node_c.compute_bound()
        node_d = Node(MyProblem(lb_value=LB_LOW, feasible=False))
        node_d.compute_bound()

        queue.enqueue(node_a)  # lb = LB_VERY_HIGH
        queue.enqueue(node_b)  # lb drops to LB_HIGH
        queue.enqueue(node_c)  # lb drops to LB_MEDIUM
        queue.enqueue(node_d)  # lb drops to LB_LOW

        # Only node_d should be the bound
        result = queue.get_lower_bound()
        assert result is node_d
        assert result.lb == LB_LOW

        # Higher-lb nodes must NOT be in bound_nodes
        bound = queue.bound_nodes
        assert node_a not in bound
        assert node_b not in bound
        assert node_c not in bound
        assert node_d in bound

    @staticmethod
    def test_bound_nodes_collects_all_equal_lb_nodes() -> None:
        """All nodes sharing the minimum lb are tracked in bound_nodes."""
        queue: BestFirstSearch[MyProblem] = BestFirstSearch()
        n1 = Node(MyProblem(lb_value=LB_LOW, feasible=False))
        n1.compute_bound()
        n2 = Node(MyProblem(lb_value=LB_LOW, feasible=False))
        n2.compute_bound()
        n3 = Node(MyProblem(lb_value=LB_MEDIUM, feasible=False))
        n3.compute_bound()

        queue.enqueue(n1)
        queue.enqueue(n2)
        queue.enqueue(n3)  # higher lb — must NOT enter bound_nodes

        bound = queue.bound_nodes
        assert n1 in bound
        assert n2 in bound
        assert n3 not in bound

    @staticmethod
    def test_bound_nodes_updated_after_sole_bound_node_dequeued() -> None:
        """After dequeuing the sole bound node, the next minimum is found."""
        queue: BestFirstSearch[MyProblem] = BestFirstSearch()
        node_low = Node(MyProblem(lb_value=LB_LOW, feasible=False))
        node_low.compute_bound()
        node_high = Node(MyProblem(lb_value=LB_HIGH, feasible=False))
        node_high.compute_bound()

        queue.enqueue(node_low)
        queue.enqueue(node_high)
        assert queue.get_lower_bound() is node_low

        queue.dequeue()  # pops node_low (best-first)

        result = queue.get_lower_bound()
        assert result is node_high
        assert result.lb == LB_HIGH

    @staticmethod
    def test_get_lower_bound_after_dequeue_enqueue_cycle() -> None:
        """get_lower_bound remains consistent through an enqueue/dequeue cycle.

        After dequeuing the bound node, self.lb is *not* reset.  A subsequent
        enqueue with lb > old self.lb must not be silently excluded from
        bound_nodes; get_lower_bound must trigger a full heap scan and still
        return the actual minimum.
        """
        queue: BestFirstSearch[MyProblem] = BestFirstSearch()
        low = Node(MyProblem(lb_value=LB_LOW, feasible=False))
        low.compute_bound()
        queue.enqueue(low)
        assert queue.get_lower_bound() is low  # lb = LB_LOW

        queue.dequeue()  # removes low; bound_nodes = {}, lb stays at LB_LOW

        high = Node(MyProblem(lb_value=LB_HIGH, feasible=False))
        high.compute_bound()
        queue.enqueue(high)
        # high.lb > self.lb (LB_LOW) — enqueue_bound_update does NOT add to
        # bound_nodes, so bound_nodes stays empty.  get_lower_bound must
        # perform a full heap scan and still find the correct minimum.
        result = queue.get_lower_bound()
        assert result is high
        assert result.lb == LB_HIGH
