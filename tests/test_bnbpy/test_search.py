from typing import Literal

import pytest
from myfixtures.myproblem import (
    MyProblem,
    PrimalHeuristicProblem,
    StrongerBoundProblem,
    UnboundedProblem,
)

from bnbpy.cython.manager import BaseNodeManager, FifoManager, LifoManager
from bnbpy.cython.node import Node
from bnbpy.cython.priqueue import BestPriQueue, BfsPriQueue, DfsPriQueue
from bnbpy.cython.problem import Problem
from bnbpy.cython.search import (
    BestFirstBnB,
    BranchAndBound,
    BreadthFirstBnB,
    DepthFirstBnB,
    FifoBnB,
    LifoBnB,
)
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
THREE = 3
TWO = 2
ONE = 1


class _CallbackBnB(BranchAndBound[MyProblem]):
    """Test subclass for solution_callback testing."""

    def __init__(self, problem: MyProblem) -> None:
        super().__init__(problem)
        self.callback_called = False

    def solution_callback(self, _: Node[MyProblem]) -> None:
        self.callback_called = True


class _PrePostEvalBnB(BranchAndBound[UnboundedProblem]):
    """Test subclass for pre_eval_callback testing."""

    def __init__(
        self,
        problem: UnboundedProblem,
        eval_node: Literal['in', 'out', 'both'] = 'out',
        save_tree: bool = False,
    ) -> None:
        super().__init__(problem, eval_node, save_tree)
        self.pre_eval_count = 0
        self.post_eval_count = 0

    def pre_eval_callback(self, _: Node[UnboundedProblem]) -> None:
        self.pre_eval_count += 1

    def post_eval_callback(self, _: Node[UnboundedProblem]) -> None:
        self.post_eval_count += 1


class _WarmstartProblem(MyProblem):
    """Test subclass for warmstart testing."""

    @staticmethod
    def warmstart() -> '_WarmstartProblem':
        # Return a feasible problem with known lb
        return _WarmstartProblem(lb_value=WARMSTART_LB, feasible=True)


@pytest.mark.core
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
        problem = MyProblem(lb_value=SIMPLE_LB, feasible=False)
        bnb = BranchAndBound(problem)
        assert bnb.rtol == DEFAULT_RTOL
        assert bnb.atol == DEFAULT_ATOL
        assert bnb.solution.status == OptStatus.NO_SOLUTION
        assert bnb.explored == 0
        assert bnb.incumbent is None
        assert bnb.bound_node is None

    @staticmethod
    def test_initialization_with_params() -> None:
        """Test BranchAndBound initialization with custom parameters."""
        problem = MyProblem(lb_value=SIMPLE_LB, feasible=False)
        bnb = BranchAndBound(problem, save_tree=True)
        assert bnb.solution.status == OptStatus.NO_SOLUTION
        assert bnb.rtol == DEFAULT_RTOL
        assert bnb.atol == DEFAULT_ATOL
        assert bnb.save_tree is True

    @staticmethod
    def test_solve_rtol_override() -> None:
        """Test that solve(rtol=X) permanently updates self.rtol."""
        problem = MyProblem(lb_value=SIMPLE_LB, feasible=True)
        bnb = BranchAndBound(problem)
        assert bnb.rtol == DEFAULT_RTOL
        assert bnb.atol == DEFAULT_ATOL
        bnb.solve(rtol=CUSTOM_RTOL, atol=CUSTOM_ATOL)
        assert bnb.rtol == CUSTOM_RTOL
        assert bnb.atol == CUSTOM_ATOL

    @staticmethod
    def test_ub_property_no_incumbent() -> None:
        """Test that ub returns infinity when no incumbent exists."""
        bnb = BranchAndBound(MyProblem(lb_value=SIMPLE_LB, feasible=False))
        assert bnb.ub == float('inf')

    @staticmethod
    def test_ub_property_with_incumbent(feasible_problem: MyProblem) -> None:
        """Test that ub returns incumbent lb when incumbent exists."""
        bnb = BranchAndBound(feasible_problem)
        node = Node(feasible_problem)
        node.compute_bound()
        bnb.incumbent = node
        assert bnb.ub == FEASIBLE_LB

    @staticmethod
    def test_lb_property_no_bound_node() -> None:
        """Test that lb returns -infinity when no bound node exists."""
        bnb = BranchAndBound(MyProblem(lb_value=SIMPLE_LB, feasible=False))
        assert bnb.lb == -float('inf')

    @staticmethod
    def test_lb_property_with_bound_node(simple_problem: MyProblem) -> None:
        """Test that lb returns bound node lb when bound node exists."""
        bnb = BranchAndBound(simple_problem)
        node = Node(simple_problem)
        node.compute_bound()
        bnb.bound_node = node
        assert bnb.lb == SIMPLE_LB

    @staticmethod
    def test_enqueue_dequeue(simple_problem: MyProblem) -> None:
        """Test that enqueue and dequeue work correctly."""
        bnb = BranchAndBound(simple_problem)
        node = Node(simple_problem)
        bnb.enqueue(node)
        dequeued = bnb.dequeue()
        assert dequeued is node

    @staticmethod
    def test_set_solution(feasible_problem: MyProblem) -> None:
        """Test that set_solution updates incumbent."""
        bnb = BranchAndBound(feasible_problem)
        node = Node(feasible_problem)
        node.compute_bound()
        node.check_feasible()
        bnb.set_solution(node)
        assert bnb.incumbent is node
        assert bnb.ub == FEASIBLE_LB

    @staticmethod
    def test_fathom(simple_problem: MyProblem) -> None:
        """Test that fathom sets node status to FATHOM."""
        bnb = BranchAndBound(simple_problem, save_tree=True)
        node = Node(simple_problem)
        bnb.fathom(node)
        assert node.solution.status == OptStatus.FATHOM


@pytest.mark.core
@pytest.mark.search
class TestBranchAndBoundSolve:
    """Test class for BranchAndBound solve functionality."""

    @staticmethod
    def test_solve_simple() -> None:
        """Test solving a simple problem."""
        problem = MyProblem(lb_value=FEASIBLE_LB, feasible=True)
        bnb = BranchAndBound(problem)
        result = bnb.solve()
        assert result.solution.status == OptStatus.OPTIMAL
        assert result.solution.cost == FEASIBLE_LB

    @staticmethod
    def test_solve_with_maxiter() -> None:
        """Test solving with iteration limit."""
        problem = UnboundedProblem()
        bnb = BranchAndBound(problem)
        _ = bnb.solve(maxiter=MAX_ITER)
        # Should stop due to iteration limit
        assert bnb.explored == MAX_ITER

    @staticmethod
    def test_solve_resume() -> None:
        """Test that a second solve() resumes from where the first stopped."""
        problem = UnboundedProblem()
        bnb = BranchAndBound(problem)
        bnb.solve(maxiter=TWO)
        explored_after_first = bnb.explored
        assert explored_after_first == TWO
        bnb.solve(maxiter=THREE)
        assert bnb.explored == explored_after_first + THREE

    @staticmethod
    def test_reset_clears_state() -> None:
        """Test that reset() clears the search state for a fresh solve."""
        problem = UnboundedProblem()
        bnb = BranchAndBound(problem)
        bnb.solve(maxiter=THREE)
        assert bnb.root is not None
        assert bnb.explored == THREE
        bnb.reset()
        assert bnb.root is None
        assert bnb.explored == 0
        # Second solve starts fresh
        bnb.solve(maxiter=TWO)
        assert bnb.explored == TWO

    @staticmethod
    def test_branch_with_tree() -> None:
        """Test that branch creates and enqueues child nodes."""
        problem = UnboundedProblem()
        bnb = BranchAndBound(problem, eval_node='out', save_tree=True)
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
        bnb = BranchAndBound(problem, eval_node='out', save_tree=False)
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
        bnb = BranchAndBound(problem)
        result = bnb.solve()
        assert result.solution.status == OptStatus.OPTIMAL
        assert result.solution.cost == SIMPLE_LB
        assert bnb.explored == 1  # Should only explore root

    @staticmethod
    def test_gap_calculation() -> None:
        """Test that gap is calculated correctly."""
        problem = _WarmstartProblem(lb_value=SIMPLE_LB, feasible=False)
        bnb = BranchAndBound(problem)
        _ = bnb.solve(maxiter=0)
        # Optimal solution should have gap = 0
        assert bnb.gap == (WARMSTART_LB - SIMPLE_LB) / WARMSTART_LB


@pytest.mark.core
@pytest.mark.search
class TestBranchAndBoundCallbacks:
    """Test class for BranchAndBound callback functionality."""

    @staticmethod
    def test_solution_callback() -> None:
        """Test that solution_callback is called when solution is found."""
        problem = MyProblem(lb_value=SIMPLE_LB, feasible=True)
        bnb = _CallbackBnB(problem)
        _ = bnb.solve()
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
        bnb = _PrePostEvalBnB(problem, eval_node=eval_node)
        result = bnb.solve(maxiter=BRANCH_UNBOUNDED)
        assert result.solution.status == OptStatus.INFEASIBLE
        assert bnb.pre_eval_count == expected
        assert bnb.post_eval_count == expected

    @staticmethod
    def test_warmstart() -> None:
        """Test that warmstart is used when available."""
        problem = _WarmstartProblem(lb_value=SIMPLE_LB, feasible=False)
        bnb = BranchAndBound(problem)
        # No bnb iterations! First solution is used
        res = bnb.solve(maxiter=0)
        # Should use warmstart solution
        assert bnb.ub == WARMSTART_LB
        assert res.solution.status == OptStatus.FEASIBLE


class _PrimalHeuristicBnB(BranchAndBound[PrimalHeuristicProblem]):
    """BnB that invokes primal_heuristic from pre_eval_callback."""

    def pre_eval_callback(self, node: Node[PrimalHeuristicProblem]) -> None:
        self.primal_heuristic(node)


class _UpgradeBoundBnB(BranchAndBound[StrongerBoundProblem]):
    """BnB that invokes upgrade_bound from pre_eval_callback."""

    def pre_eval_callback(self, node: Node[StrongerBoundProblem]) -> None:
        self.upgrade_bound(node)


@pytest.mark.core
@pytest.mark.search
class TestBranchAndBoundPrimalAndBound:
    """Tests for BranchAndBound.primal_heuristic and .upgrade_bound methods."""

    @staticmethod
    def test_primal_heuristic_no_child() -> None:
        """primal_heuristic does nothing when node yields None."""
        problem = MyProblem(lb_value=SIMPLE_LB, feasible=False)
        bnb = BranchAndBound(problem)
        node = Node(problem)
        node.compute_bound()
        bnb.primal_heuristic(node)
        assert bnb.incumbent is None

    @staticmethod
    def test_primal_heuristic_updates_incumbent() -> None:
        """primal_heuristic sets incumbent when child is feasible."""
        problem = PrimalHeuristicProblem(lb_value=SIMPLE_LB, feasible=False)
        bnb = BranchAndBound(problem)
        node = Node(problem)
        node.compute_bound()
        bnb.primal_heuristic(node)
        assert bnb.incumbent is not None
        assert bnb.ub == SIMPLE_LB

    @staticmethod
    def test_primal_heuristic_skips_worse_lb() -> None:
        """primal_heuristic skips child when child.lb >= current ub."""
        incumbent_problem = MyProblem(lb_value=SIMPLE_LB, feasible=True)
        heur_problem = PrimalHeuristicProblem(
            lb_value=SIMPLE_LB, feasible=False
        )
        bnb: BranchAndBound[Problem] = BranchAndBound(heur_problem)
        # Manually set an incumbent with lower cost
        incumbent_node: Node[Problem] = Node(incumbent_problem)
        incumbent_node.compute_bound()
        incumbent_node.check_feasible()
        bnb.incumbent = incumbent_node
        # Child lb equals current ub — should be skipped
        heur_problem = PrimalHeuristicProblem(
            lb_value=SIMPLE_LB, feasible=False
        )
        heur_node: Node[Problem] = Node(heur_problem)
        heur_node.compute_bound()
        bnb.primal_heuristic(heur_node)
        # Incumbent should remain the original one
        assert bnb.incumbent is incumbent_node

    @staticmethod
    def test_primal_heuristic_called_from_callback() -> None:
        """Solve with _PrimalHeuristicBnB finds solution via heuristic."""
        problem = PrimalHeuristicProblem(lb_value=SIMPLE_LB, feasible=False)
        bnb = _PrimalHeuristicBnB(problem)
        result = bnb.solve()
        assert result.solution.status == OptStatus.OPTIMAL
        assert result.solution.cost == SIMPLE_LB

    @staticmethod
    def test_upgrade_bound_delegates_to_node() -> None:
        """BranchAndBound.upgrade_bound raises node.lb via stronger_bound."""
        problem = StrongerBoundProblem(lb_value=SIMPLE_LB)
        bnb = BranchAndBound(problem)
        node = Node(problem)
        node.compute_bound()
        lb_before = node.lb
        bnb.upgrade_bound(node)
        assert node.lb > lb_before

    @staticmethod
    def test_upgrade_bound_no_change_base_problem() -> None:
        """upgrade_bound leaves lb unchanged for base MyProblem."""
        problem = MyProblem(lb_value=SIMPLE_LB)
        bnb = BranchAndBound(problem)
        node = Node(problem)
        node.compute_bound()
        lb_before = node.lb
        bnb.upgrade_bound(node)
        assert node.lb == lb_before

    @staticmethod
    def test_upgrade_bound_in_callback_prunes_earlier() -> None:
        """_UpgradeBoundBnB explores fewer nodes due to tighter bounds."""
        # A feasible problem at root provides an upper bound,
        # then a stronger-bound variant is used as the search problem
        # so upgrade_bound tightens lb -> earlier pruning.
        ub_value = FEASIBLE_LB  # ub set by warmstart

        class _WarmstartStrong(StrongerBoundProblem):
            @staticmethod
            def warmstart() -> '_WarmstartStrong':
                return _WarmstartStrong(lb_value=ub_value, feasible=True)

        base_problem = StrongerBoundProblem(lb_value=SIMPLE_LB, feasible=False)
        upgrade_problem = _WarmstartStrong(lb_value=SIMPLE_LB, feasible=False)
        bnb_base = BranchAndBound(base_problem)
        bnb_upgrade = _UpgradeBoundBnB(upgrade_problem)
        result_base = bnb_base.solve()
        result_upgrade = bnb_upgrade.solve()
        # Both reach optimal; upgrade variant explores <= base variant
        assert result_base.solution.status == OptStatus.OPTIMAL
        assert result_upgrade.solution.status == OptStatus.OPTIMAL
        assert bnb_upgrade.explored <= bnb_base.explored


class TestGenericBehavior:
    @staticmethod
    def test_raises_type_error_on_wrong_generic() -> None:
        """
        Test that BranchAndBound raises
        TypeError when parameterized with non-Problem.
        """
        with pytest.raises(TypeError):
            BranchAndBound[int]  # type: ignore

    @staticmethod
    def test_is_okay_with_problem() -> None:
        """
        Test that BranchAndBound can be
        parameterized with a Problem subclass.
        """

        bnb = BranchAndBound[MyProblem]
        assert bnb is BranchAndBound, (
            'BranchAndBound[MyProblem] should return the class itself'
        )


@pytest.mark.core
@pytest.mark.search
class TestManagerStrategy:
    """Tests for the manager strategy pattern in BranchAndBound."""

    @staticmethod
    def test_default_manager_is_dfs() -> None:
        """Default manager should be DfsPriQueue."""
        problem = MyProblem(lb_value=SIMPLE_LB, feasible=True)
        bnb = BranchAndBound(problem)
        assert isinstance(bnb.manager, DfsPriQueue)

    @staticmethod
    def test_custom_manager_injected() -> None:
        """A custom manager passed at construction should be used."""
        problem = MyProblem(lb_value=SIMPLE_LB, feasible=True)
        custom: BfsPriQueue[MyProblem] = BfsPriQueue()
        bnb = BranchAndBound(problem, manager=custom)
        assert bnb.manager is custom

    @staticmethod
    def test_manager_is_base_node_manager() -> None:
        """manager attribute must be a BaseNodeManager instance."""
        problem = MyProblem(lb_value=SIMPLE_LB, feasible=True)
        bnb = BranchAndBound(problem)
        assert isinstance(bnb.manager, BaseNodeManager)

    @staticmethod
    @pytest.mark.parametrize(
        ('strategy', 'expected_type'),
        [
            ('dfs', DfsPriQueue),
            ('bfs', BfsPriQueue),
            ('best', BestPriQueue),
            ('lifo', LifoManager),
            ('fifo', FifoManager),
        ],
    )
    def test_build_manager_factory(strategy: str, expected_type: type) -> None:
        """build_manager returns the correct manager for each strategy."""
        mgr = BranchAndBound.build_manager(strategy)
        assert isinstance(mgr, expected_type)

    @staticmethod
    def test_build_manager_case_insensitive() -> None:
        """build_manager should accept upper-case strategy names."""
        mgr = BranchAndBound.build_manager('DFS')
        assert isinstance(mgr, DfsPriQueue)

    @staticmethod
    def test_build_manager_unknown_raises() -> None:
        """build_manager raises ValueError for unknown strategy."""
        with pytest.raises(ValueError, match='Unknown strategy'):
            BranchAndBound.build_manager('unknown')

    @staticmethod
    def test_build_manager_solve_equivalence() -> None:
        """Using build_manager('bfs') gives same result as BreadthFirstBnB."""
        problem1 = MyProblem(lb_value=FEASIBLE_LB, feasible=True)
        problem2 = MyProblem(lb_value=FEASIBLE_LB, feasible=True)
        mgr = BranchAndBound.build_manager('bfs')
        bnb1 = BranchAndBound(problem1, manager=mgr)
        bnb2 = BreadthFirstBnB(problem2)
        res1 = bnb1.solve()
        res2 = bnb2.solve()
        assert res1.solution.status == res2.solution.status
        assert res1.solution.cost == res2.solution.cost


@pytest.mark.core
@pytest.mark.search
class TestSubclassStrategies:
    """Tests for BnB subclass variants using different manager strategies."""

    @staticmethod
    def test_depth_first_bnb_is_alias() -> None:
        """DepthFirstBnB should use a DfsPriQueue manager."""
        problem = MyProblem(lb_value=SIMPLE_LB, feasible=True)
        bnb = DepthFirstBnB(problem)
        assert isinstance(bnb.manager, DfsPriQueue)

    @staticmethod
    def test_breadth_first_bnb_manager() -> None:
        """BreadthFirstBnB should use a BfsPriQueue manager."""
        problem = MyProblem(lb_value=SIMPLE_LB, feasible=True)
        bnb = BreadthFirstBnB(problem)
        assert isinstance(bnb.manager, BfsPriQueue)

    @staticmethod
    def test_best_first_bnb_manager() -> None:
        """BestFirstBnB should use a BestPriQueue manager."""
        problem = MyProblem(lb_value=SIMPLE_LB, feasible=True)
        bnb = BestFirstBnB(problem)
        assert isinstance(bnb.manager, BestPriQueue)

    @staticmethod
    def test_lifo_bnb_manager() -> None:
        """LifoBnB should use a LifoManager."""
        problem = MyProblem(lb_value=SIMPLE_LB, feasible=True)
        bnb = LifoBnB(problem)
        assert isinstance(bnb.manager, LifoManager)

    @staticmethod
    def test_fifo_bnb_manager() -> None:
        """FifoBnB should use a FifoManager."""
        problem = MyProblem(lb_value=SIMPLE_LB, feasible=True)
        bnb = FifoBnB(problem)
        assert isinstance(bnb.manager, FifoManager)

    @staticmethod
    @pytest.mark.parametrize(
        'bnb_class',
        [DepthFirstBnB, BreadthFirstBnB, BestFirstBnB, LifoBnB, FifoBnB],
    )
    def test_all_subclasses_solve_feasible(bnb_class: type) -> None:
        """All BnB variants should solve a trivially feasible problem."""
        problem = MyProblem(lb_value=FEASIBLE_LB, feasible=True)
        bnb = bnb_class(problem)
        result = bnb.solve()
        assert result.solution.status == OptStatus.OPTIMAL
        assert result.solution.cost == FEASIBLE_LB
