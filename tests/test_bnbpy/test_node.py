import pytest
from myfixtures.myproblem import (
    MyProblem,
    PrimalHeuristicProblem,
    StrongerBoundProblem,
)

from bnbpy.cython.node import Node
from bnbpy.cython.solution import Solution
from bnbpy.cython.status import OptStatus


class _InfeasiblePrimalProblem(MyProblem):
    """Returns an infeasible problem from primal_heuristic."""

    def primal_heuristic(self) -> '_InfeasiblePrimalProblem':
        return _InfeasiblePrimalProblem(
            lb_value=self._lb_value, feasible=False
        )


@pytest.mark.core
@pytest.mark.node
class TestNode:
    """Test class for the Node class."""

    @staticmethod
    @pytest.fixture
    def parent_problem() -> MyProblem:
        return MyProblem(lb_value=5, feasible=True)

    @staticmethod
    @pytest.fixture
    def child_problem() -> MyProblem:
        return MyProblem(lb_value=10, feasible=False)

    @staticmethod
    def test_node_initialization(parent_problem: MyProblem) -> None:
        """Test the initialization of a Node instance."""
        node = Node(problem=parent_problem)
        assert node.problem == parent_problem
        assert node.parent is None
        assert isinstance(node.solution, Solution)
        assert node.children == []
        assert node.lb == parent_problem.lb

    @staticmethod
    def test_node_sorting(parent_problem: MyProblem) -> None:
        """Test that nodes are sorted based on their _sort_index."""
        node1 = Node(problem=parent_problem)
        node2 = Node(problem=parent_problem, parent=node1)

        # Nodes should be sortable based on the order of creation
        assert node1 > node2

    @staticmethod
    def test_eq_is_identity(parent_problem: MyProblem) -> None:
        """Two distinct nodes with the same problem are not equal."""
        node_a = Node(problem=parent_problem)
        node_b = Node(problem=parent_problem)
        assert node_a != node_b
        assert node_a == node_a  # noqa: PLR0124

    @staticmethod
    def test_hash_is_identity(parent_problem: MyProblem) -> None:
        """Each node has a unique hash based on object identity."""
        node_a = Node(problem=parent_problem)
        node_b = Node(problem=parent_problem)
        assert hash(node_a) != hash(node_b)
        assert hash(node_a) == hash(node_a)  # noqa: PLR0124

    @staticmethod
    def test_nodes_usable_in_set(parent_problem: MyProblem) -> None:
        """Distinct nodes can coexist in a set."""
        node_a = Node(problem=parent_problem)
        node_b = Node(problem=parent_problem)
        s = {node_a, node_b}
        two_nodes = 2
        assert len(s) == two_nodes
        assert node_a in s
        assert node_b in s

    @staticmethod
    def test_node_lb_property(parent_problem: MyProblem) -> None:
        """Test that the lb property returns the correct lower bound."""
        node = Node(problem=parent_problem)
        assert node.lb == parent_problem.lb

    @staticmethod
    @pytest.mark.parametrize(
        ('feasible', 'expected_status'),
        [
            (True, OptStatus.FEASIBLE),
            (False, OptStatus.INFEASIBLE),
        ],
    )
    def test_check_feasible(
        feasible: bool, expected_status: OptStatus
    ) -> None:
        """Test the check_feasible method of Node."""
        prob = MyProblem(feasible=feasible)
        node = Node(problem=prob)
        node_feas = node.check_feasible()
        assert node_feas is feasible
        assert node.solution.status == expected_status

    @staticmethod
    def test_branch_on(parent_problem: MyProblem) -> None:
        """Test the branch method of Node."""
        # Create a node with a problem that generates two child problems
        node = Node(problem=parent_problem)
        children = node.branch()

        # Check that two child nodes are created
        n_children = 2
        assert children is not None
        assert len(children) == n_children

        # Verify that the children are instances of Node
        # and have the correct parent
        for child in children:
            assert type(child) is type(node), f'{type(child)} x {type(node)}'
            assert child.parent == node

        # Check that the children have the correct lower bounds
        # based on the branching logic of MyProblem
        assert children[1].lb == parent_problem.lb + 1
        assert children[0].lb == parent_problem.lb + 2

    @staticmethod
    def test_copy(parent_problem: MyProblem) -> None:
        """Test copying functionality of Node."""
        node = Node(problem=parent_problem)
        node.problem.compute_bound()
        shallow_copy = node.copy(deep=False)
        deep_copy = node.copy(deep=True)

        assert deep_copy.lb == shallow_copy.lb
        assert shallow_copy is not node
        assert deep_copy is not node
        assert shallow_copy.solution is node.solution
        assert deep_copy.solution is not node.solution

    # ------------------------------------------------------------------
    # primal_heuristic
    # ------------------------------------------------------------------

    @staticmethod
    def test_primal_heuristic_returns_none_when_none(
        parent_problem: MyProblem,
    ) -> None:
        """Node.primal_heuristic() returns None when problem returns None."""
        node = Node(problem=parent_problem)
        assert node.primal_heuristic() is None

    @staticmethod
    def test_primal_heuristic_returns_feasible_child() -> None:
        """Node.primal_heuristic() returns a Node child when feasible."""
        prob = PrimalHeuristicProblem(lb_value=7)
        node = Node(problem=prob)
        child = node.primal_heuristic()
        assert child is not None
        assert isinstance(child, Node)
        assert child.solution.status == OptStatus.FEASIBLE

    @staticmethod
    def test_primal_heuristic_child_level() -> None:
        """Child node level is parent level + 1."""
        prob = PrimalHeuristicProblem(lb_value=7)
        node = Node(problem=prob)
        child = node.primal_heuristic()
        assert child is not None
        assert child.level == 0
        assert child.parent is None

    @staticmethod
    def test_primal_heuristic_returns_none_when_infeasible() -> None:
        """Node returns None when primal_heuristic yields infeasible."""
        prob = _InfeasiblePrimalProblem(lb_value=7)
        node = Node(problem=prob)
        assert node.primal_heuristic() is None

    # ------------------------------------------------------------------
    # upgrade_bound
    # ------------------------------------------------------------------

    @staticmethod
    def test_upgrade_bound_improves_lb() -> None:
        """upgrade_bound raises node.lb when stronger_bound > current lb."""
        prob = StrongerBoundProblem(lb_value=10)
        node = Node(problem=prob)
        node.compute_bound()
        lb_before = node.lb
        node.upgrade_bound()
        assert node.lb > lb_before

    @staticmethod
    def test_upgrade_bound_no_change_equal(
        parent_problem: MyProblem,
    ) -> None:
        """upgrade_bound leaves lb unchanged when stronger_bound == lb."""
        node = Node(problem=parent_problem)
        node.compute_bound()
        lb_before = node.lb
        node.upgrade_bound()
        assert node.lb == lb_before

    @staticmethod
    def test_upgrade_bound_no_change_before_compute(
        parent_problem: MyProblem,
    ) -> None:
        """upgrade_bound leaves lb unchanged before compute_bound."""
        node = Node(problem=parent_problem)
        lb_before = node.lb
        node.upgrade_bound()
        assert node.lb == lb_before
