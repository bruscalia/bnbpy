from typing import Literal

import pytest
from fixtures.myproblem import MyProblem, UnboundedProblem

from bnbpy.cython.node import Node
from bnbpy.cython.search import BranchAndBound
from bnbpy.cython.status import OptStatus

# Test constants
DEFAULT_RTOL = 1e-4
DEFAULT_ATOL = 1e-4
CUSTOM_RTOL = 1e-3
CUSTOM_ATOL = 1e-2
SIMPLE_LB = 5
FEASIBLE_LB = 10
WARMSTART_LB = 8
MAX_ITER = 5
BRANCH_UNBOUNDED = 3


class _CallbackBnB(BranchAndBound):
    """Test subclass for solution_callback testing."""

    def __init__(self) -> None:
        super().__init__()
        self.callback_called = False

    def solution_callback(self, _: Node) -> None:
        self.callback_called = True


class _PrePostEvalBnB(BranchAndBound):
    """Test subclass for pre_eval_callback testing."""

    def __init__(
        self,
        rtol: float = 1e-4,
        atol: float = 1e-4,
        eval_node: Literal['in', 'out', 'both'] = 'out',
        save_tree: bool = False,
    ) -> None:
        super().__init__(rtol, atol, eval_node, save_tree)
        self.pre_eval_count = 0
        self.post_eval_count = 0

    def pre_eval_callback(self, _: Node) -> None:
        self.pre_eval_count += 1

    def post_eval_callback(self, _: Node) -> None:
        self.post_eval_count += 1


class _WarmstartProblem(MyProblem):
    """Test subclass for warmstart testing."""

    @staticmethod
    def warmstart() -> '_WarmstartProblem':
        # Return a feasible problem with known lb
        return _WarmstartProblem(lb_value=WARMSTART_LB, feasible=True)


@pytest.mark.search
class TestBranchAndBoundBasic:
    """Test class for basic BranchAndBound functionality."""

    @staticmethod
    @pytest.fixture
    def simple_problem() -> MyProblem:
        return MyProblem(lb_value=SIMPLE_LB, feasible=False)

    @staticmethod
    @pytest.fixture
    def feasible_problem() -> MyProblem:
        return MyProblem(lb_value=FEASIBLE_LB, feasible=True)

    @staticmethod
    def test_initialization() -> None:
        """Test the initialization of a BranchAndBound instance."""
        bnb = BranchAndBound()
        assert bnb.rtol == DEFAULT_RTOL
        assert bnb.atol == DEFAULT_ATOL
        assert bnb.solution.status == OptStatus.NO_SOLUTION
        assert bnb.explored == 0
        assert bnb.incumbent is None
        assert bnb.bound_node is None

    @staticmethod
    def test_initialization_with_params() -> None:
        """Test BranchAndBound initialization with custom parameters."""
        bnb = BranchAndBound(
            rtol=CUSTOM_RTOL, atol=CUSTOM_ATOL, save_tree=True
        )
        assert bnb.solution.status == OptStatus.NO_SOLUTION
        assert bnb.rtol == CUSTOM_RTOL
        assert bnb.atol == CUSTOM_ATOL
        assert bnb.save_tree is True

    @staticmethod
    def test_ub_property_no_incumbent() -> None:
        """Test that ub returns infinity when no incumbent exists."""
        bnb = BranchAndBound()
        assert bnb.ub == float('inf')

    @staticmethod
    def test_ub_property_with_incumbent(feasible_problem: MyProblem) -> None:
        """Test that ub returns incumbent lb when incumbent exists."""
        bnb = BranchAndBound()
        node = Node(feasible_problem)
        node.compute_bound()
        bnb.incumbent = node
        assert bnb.ub == FEASIBLE_LB

    @staticmethod
    def test_lb_property_no_bound_node() -> None:
        """Test that lb returns -infinity when no bound node exists."""
        bnb = BranchAndBound()
        assert bnb.lb == -float('inf')

    @staticmethod
    def test_lb_property_with_bound_node(simple_problem: MyProblem) -> None:
        """Test that lb returns bound node lb when bound node exists."""
        bnb = BranchAndBound()
        node = Node(simple_problem)
        node.compute_bound()
        bnb.bound_node = node
        assert bnb.lb == SIMPLE_LB

    @staticmethod
    def test_enqueue_dequeue(simple_problem: MyProblem) -> None:
        """Test that enqueue and dequeue work correctly."""
        bnb = BranchAndBound()
        node = Node(simple_problem)
        bnb.enqueue(node)
        dequeued = bnb.dequeue()
        assert dequeued is node

    @staticmethod
    def test_set_solution(feasible_problem: MyProblem) -> None:
        """Test that set_solution updates incumbent."""
        bnb = BranchAndBound()
        node = Node(feasible_problem)
        node.compute_bound()
        node.check_feasible()
        bnb.set_solution(node)
        assert bnb.incumbent is node
        assert bnb.ub == FEASIBLE_LB

    @staticmethod
    def test_fathom(simple_problem: MyProblem) -> None:
        """Test that fathom sets node status to FATHOM."""
        bnb = BranchAndBound(save_tree=True)
        node = Node(simple_problem)
        bnb.fathom(node)
        assert node.solution.status == OptStatus.FATHOM


@pytest.mark.search
class TestBranchAndBoundSolve:
    """Test class for BranchAndBound solve functionality."""

    @staticmethod
    def test_solve_simple() -> None:
        """Test solving a simple problem."""
        problem = MyProblem(lb_value=FEASIBLE_LB, feasible=True)
        bnb = BranchAndBound()
        result = bnb.solve(problem)
        assert result.solution.status == OptStatus.OPTIMAL
        assert result.solution.cost == FEASIBLE_LB

    @staticmethod
    def test_solve_with_maxiter() -> None:
        """Test solving with iteration limit."""
        problem = UnboundedProblem()
        bnb = BranchAndBound()
        _ = bnb.solve(problem, maxiter=MAX_ITER)
        # Should stop due to iteration limit
        assert bnb.explored == MAX_ITER

    @staticmethod
    def test_branch_with_tree() -> None:
        """Test that branch creates and enqueues child nodes."""
        problem = UnboundedProblem()
        bnb = BranchAndBound(eval_node='out', save_tree=True)
        node = Node(problem)
        node.compute_bound()
        bnb.branch(node)
        # Should have enqueued 2 children
        child1 = bnb.dequeue()
        child2 = bnb.dequeue()
        assert child1 is not None
        assert child2 is not None
        assert child1.parent is node
        assert child2.parent is node

    @staticmethod
    def test_branch_clear_tree() -> None:
        """Test that branch creates and enqueues child nodes."""
        problem = UnboundedProblem()
        bnb = BranchAndBound(eval_node='out', save_tree=False)
        node = Node(problem)
        node.compute_bound()
        bnb.branch(node)
        # Should have enqueued 2 children
        child1 = bnb.dequeue()
        child2 = bnb.dequeue()
        assert child1 is not None
        assert child2 is not None
        assert child1.parent is None
        assert child2.parent is None

    @staticmethod
    def test_optimality_check() -> None:
        """Test that optimal solution is found for simple case."""
        # Create a problem with feasible solution at root
        problem = MyProblem(lb_value=SIMPLE_LB, feasible=True)
        bnb = BranchAndBound()
        result = bnb.solve(problem)
        assert result.solution.status == OptStatus.OPTIMAL
        assert result.solution.cost == SIMPLE_LB
        assert bnb.explored == 1  # Should only explore root

    @staticmethod
    def test_gap_calculation() -> None:
        """Test that gap is calculated correctly."""
        problem = _WarmstartProblem(lb_value=SIMPLE_LB, feasible=False)
        bnb = BranchAndBound()
        _ = bnb.solve(problem, maxiter=0)
        # Optimal solution should have gap = 0
        assert bnb.gap == (WARMSTART_LB - SIMPLE_LB) / WARMSTART_LB


@pytest.mark.search
class TestBranchAndBoundCallbacks:
    """Test class for BranchAndBound callback functionality."""

    @staticmethod
    def test_solution_callback() -> None:
        """Test that solution_callback is called when solution is found."""
        problem = MyProblem(lb_value=SIMPLE_LB, feasible=True)
        bnb = _CallbackBnB()
        _ = bnb.solve(problem)
        assert bnb.callback_called is True

    @staticmethod
    @pytest.mark.parametrize(
        ('eval_node', 'expected'),
        [('in', 7), ('out', 3), ('both', 10)],
    )
    def test_eval_node_modes(
        eval_node: Literal['in', 'out', 'both'], expected: int
    ) -> None:
        """Test different node evaluation modes."""
        problem = UnboundedProblem()
        bnb = _PrePostEvalBnB(eval_node=eval_node)
        result = bnb.solve(problem, maxiter=BRANCH_UNBOUNDED)
        assert result.solution.status == OptStatus.INFEASIBLE
        assert bnb.pre_eval_count == expected
        assert bnb.post_eval_count == expected

    @staticmethod
    def test_warmstart() -> None:
        """Test that warmstart is used when available."""
        problem = _WarmstartProblem(lb_value=SIMPLE_LB, feasible=False)
        bnb = BranchAndBound()
        # No bnb iterations! First solution is used
        res = bnb.solve(problem, maxiter=0)
        # Should use warmstart solution
        assert bnb.ub == WARMSTART_LB
        assert res.solution.status == OptStatus.FEASIBLE
