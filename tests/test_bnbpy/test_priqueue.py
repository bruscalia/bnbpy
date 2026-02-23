import pytest
from myfixtures.myproblem import MyProblem

from bnbpy.cython.node import Node
from bnbpy.cython.priqueue import (
    BestPriQueue,
    BFSPriQueue,
    DFSPriQueue,
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
class TestHeapPriQueue:
    """Test class for HeapPriQueue functionality using DFSPriQueue."""

    @staticmethod
    @pytest.fixture
    def empty_queue() -> DFSPriQueue:
        """Use DFSPriQueue as concrete implementation."""
        return DFSPriQueue()

    @staticmethod
    @pytest.fixture
    def node_low() -> Node:
        problem = MyProblem(lb_value=LB_LOW, feasible=False)
        node = Node(problem)
        node.compute_bound()
        return node

    @staticmethod
    @pytest.fixture
    def node_medium() -> Node:
        problem = MyProblem(lb_value=LB_MEDIUM, feasible=False)
        node = Node(problem)
        node.compute_bound()
        return node

    @staticmethod
    @pytest.fixture
    def node_high() -> Node:
        problem = MyProblem(lb_value=LB_HIGH, feasible=False)
        node = Node(problem)
        node.compute_bound()
        return node

    @staticmethod
    def test_initialization(empty_queue: DFSPriQueue) -> None:
        """Test the initialization of a HeapPriQueue instance."""
        assert empty_queue.not_empty() is False

    @staticmethod
    def test_not_empty_after_enqueue(
        empty_queue: DFSPriQueue, node_low: Node
    ) -> None:
        """Test that not_empty returns True after enqueueing a node."""
        empty_queue.enqueue(node_low)
        assert empty_queue.not_empty() is True

    @staticmethod
    def test_dequeue_empty_queue(empty_queue: DFSPriQueue) -> None:
        """Test that dequeue returns None for an empty queue."""
        result = empty_queue.dequeue()
        assert result is None

    @staticmethod
    def test_get_lower_bound_empty_queue(empty_queue: DFSPriQueue) -> None:
        """Test that get_lower_bound returns None for an empty queue."""
        result = empty_queue.get_lower_bound()
        assert result is None

    @staticmethod
    def test_pop_lower_bound_empty_queue(empty_queue: DFSPriQueue) -> None:
        """Test that pop_lower_bound returns None for an empty queue."""
        result = empty_queue.pop_lower_bound()
        assert result is None

    @staticmethod
    def test_get_lower_bound_single_node(
        empty_queue: DFSPriQueue, node_low: Node
    ) -> None:
        """Test get_lower_bound with a single node."""
        empty_queue.enqueue(node_low)
        result = empty_queue.get_lower_bound()
        assert result is node_low
        assert result.lb == LB_LOW

    @staticmethod
    def test_get_lower_bound_multiple_nodes(
        empty_queue: DFSPriQueue,
        node_low: Node,
        node_medium: Node,
        node_high: Node,
    ) -> None:
        """Test get_lower_bound returns node with lowest lb."""
        empty_queue.enqueue(node_high)
        empty_queue.enqueue(node_low)
        empty_queue.enqueue(node_medium)
        result = empty_queue.get_lower_bound()
        assert result is node_low
        assert result.lb == LB_LOW

    @staticmethod
    def test_pop_lower_bound_removes_node(
        empty_queue: DFSPriQueue, node_low: Node, node_medium: Node
    ) -> None:
        """Test that pop_lower_bound removes the node with lowest lb."""
        empty_queue.enqueue(node_medium)
        empty_queue.enqueue(node_low)
        result = empty_queue.pop_lower_bound()
        assert result is node_low
        # After popping, only medium node should remain
        assert empty_queue.not_empty() is True
        next_node = empty_queue.get_lower_bound()
        assert next_node is node_medium

    @staticmethod
    def test_clear(
        empty_queue: DFSPriQueue, node_low: Node, node_medium: Node
    ) -> None:
        """Test that clear empties the queue."""
        empty_queue.enqueue(node_low)
        empty_queue.enqueue(node_medium)
        assert empty_queue.not_empty() is True
        empty_queue.clear()
        assert empty_queue.not_empty() is False

    @staticmethod
    def test_filter_by_lb(
        empty_queue: DFSPriQueue,
        node_low: Node,
        node_medium: Node,
        node_high: Node,
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
        assert first.lb == LB_LOW
        assert second.lb == LB_MEDIUM
        assert third is None


@pytest.mark.core
@pytest.mark.priqueue
class TestDFSPriQueue:
    """Test class for DFSPriQueue (Depth-First Search) functionality."""

    @staticmethod
    @pytest.fixture
    def dfs_queue() -> DFSPriQueue:
        return DFSPriQueue()

    @staticmethod
    def test_initialization(dfs_queue: DFSPriQueue) -> None:
        """Test the initialization of a DFSPriQueue instance."""
        assert dfs_queue.not_empty() is False

    @staticmethod
    def test_dfs_ordering() -> None:
        """Test that DFS queue dequeues deeper nodes first."""
        queue = DFSPriQueue()
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

        assert first.level == LEVEL_GRANDCHILD  # grandchild
        assert second.level == LEVEL_CHILD  # child
        assert third.level == LEVEL_ROOT  # root

    @staticmethod
    def test_dfs_same_level_ordering() -> None:
        """Test DFS ordering when nodes are at the same level."""
        queue = DFSPriQueue()
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

        assert first.lb == LB_LOW
        assert second.lb == LB_HIGH


@pytest.mark.core
@pytest.mark.priqueue
class TestBFSPriQueue:
    """Test class for BFSPriQueue (Breadth-First Search) functionality."""

    @staticmethod
    @pytest.fixture
    def bfs_queue() -> BFSPriQueue:
        return BFSPriQueue()

    @staticmethod
    def test_initialization(bfs_queue: BFSPriQueue) -> None:
        """Test the initialization of a BFSPriQueue instance."""
        assert bfs_queue.not_empty() is False

    @staticmethod
    def test_bfs_ordering() -> None:
        """Test that BFS queue dequeues shallower nodes first."""
        queue = BFSPriQueue()
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

        # Enqueue in non-BFS order
        queue.enqueue(grandchild)
        queue.enqueue(root)
        queue.enqueue(child)

        # BFS should dequeue shallowest first (lowest level)
        first = queue.dequeue()
        second = queue.dequeue()
        third = queue.dequeue()

        assert first.level == LEVEL_ROOT  # root
        assert second.level == LEVEL_CHILD  # child
        assert third.level == LEVEL_GRANDCHILD  # grandchild

    @staticmethod
    def test_bfs_same_level_ordering() -> None:
        """Test BFS ordering when nodes are at the same level."""
        queue = BFSPriQueue()
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

        assert first.lb == LB_LOW
        assert second.lb == LB_HIGH


@pytest.mark.core
@pytest.mark.priqueue
class TestBestPriQueue:
    """Test class for BestPriQueue (Best-First Search) functionality."""

    @staticmethod
    @pytest.fixture
    def best_queue() -> BestPriQueue:
        return BestPriQueue()

    @staticmethod
    def test_initialization(best_queue: BestPriQueue) -> None:
        """Test the initialization of a BestPriQueue instance."""
        assert best_queue.not_empty() is False

    @staticmethod
    def test_best_first_ordering() -> None:
        """Test that best-first queue dequeues nodes with lowest lb."""
        queue = BestPriQueue()
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

        assert first.lb == LB_LOW
        assert second.lb == LB_MEDIUM
        assert third.lb == LB_HIGH

    @staticmethod
    def test_best_first_same_lb_ordering() -> None:
        """Test best-first ordering when nodes have the same lb."""
        queue = BestPriQueue()
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

        # At same lb, should use -level as tiebreaker (deeper first)
        first = queue.dequeue()
        second = queue.dequeue()

        assert first.level == LEVEL_DEEP  # Deeper node first
        assert second.level == LEVEL_CHILD

    @staticmethod
    def test_best_first_mixed_scenario() -> None:
        """Test best-first with mixed bounds and levels."""
        queue = BestPriQueue()
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

        # Should dequeue in order: LB_LOW (deeper first), then by lb
        first = queue.dequeue()
        assert first.lb == LB_LOW
        assert first.level == LEVEL_DEEP  # Deeper of the two LB_LOW nodes

        second = queue.dequeue()
        assert second.lb == LB_LOW
        assert second.level == LEVEL_GRANDCHILD

        third = queue.dequeue()
        assert third.lb == LB_MEDIUM

        fourth = queue.dequeue()
        assert fourth.lb == LB_HIGH

        fifth = queue.dequeue()
        assert fifth.lb == LB_VERY_HIGH
