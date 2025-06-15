import pytest

from bnbpy.node import Node
from bnbpy.solution import Solution
from bnbpy.status import OptStatus
from tests.fixtures.myproblem import MyProblem


@pytest.mark.node
class TestNode:
    """Test class for the Node class."""

    @pytest.fixture
    def parent_problem(self):  # noqa: PLR6301
        return MyProblem(lb_value=5, feasible=True)

    @pytest.fixture
    def child_problem(self):  # noqa: PLR6301
        return MyProblem(lb_value=10, feasible=False)

    @staticmethod
    def test_node_initialization(parent_problem):
        """Test the initialization of a Node instance."""
        node = Node(problem=parent_problem)
        assert node.problem == parent_problem
        assert node.parent is None
        assert isinstance(node.solution, Solution)
        assert node.children == []
        assert node.lb == parent_problem.lb

    @staticmethod
    def test_node_sorting(parent_problem):
        """Test that nodes are sorted based on their _sort_index."""
        node1 = Node(problem=parent_problem)
        node2 = Node(problem=parent_problem, parent=node1)

        # Nodes should be sortable based on the order of creation
        assert node1 > node2

    @staticmethod
    def test_node_lb_property(parent_problem):
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
    def test_check_feasible(feasible, expected_status):
        """Test the check_feasible method of Node."""
        prob = MyProblem(feasible=feasible)
        node = Node(problem=prob)
        node_feas = node.check_feasible()
        assert node_feas is feasible
        assert node.solution.status == expected_status

    @staticmethod
    def test_branch_on(parent_problem: MyProblem):
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
    def test_copy(parent_problem: MyProblem):
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
