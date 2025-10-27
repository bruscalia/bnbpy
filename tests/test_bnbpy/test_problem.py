import pytest
from myfixtures.myproblem import MyProblem

from bnbpy.cython.problem import Problem
from bnbpy.cython.solution import Solution
from bnbpy.cython.status import OptStatus


@pytest.mark.problem
class TestProblem:
    @staticmethod
    def test_problem_initial_state() -> None:
        """Test that the initial state of Problem is correctly set."""
        prob = MyProblem()
        assert isinstance(prob.solution, Solution)
        assert prob.lb == -float('inf')

    @staticmethod
    def test_compute_bound(my_problem: MyProblem) -> None:
        """
        Test that compute_bound correctly calculates and sets the lower bound.
        """
        ref_value = 10
        my_problem.compute_bound()
        assert my_problem.lb == ref_value
        assert my_problem.solution.lb == ref_value
        assert my_problem.solution.status == OptStatus.RELAXATION

    @staticmethod
    def test_check_feasible(my_problem: MyProblem) -> None:
        """
        Test that check_feasible sets the correct status based on feasibility.
        """
        assert my_problem.check_feasible() is True
        assert my_problem.solution.status == OptStatus.FEASIBLE

        prob = MyProblem(feasible=False)
        assert prob.check_feasible() is False
        assert prob.solution.status == OptStatus.INFEASIBLE

    @staticmethod
    def test_branch_on() -> None:
        """Test that branch returns child problems."""
        ref_value = 5
        n_children = 2
        prob = MyProblem(lb_value=ref_value)
        children = prob.branch()
        if children is None:
            raise ValueError(
                'Branching returned None, expected child problems.'
            )
        for c in children:
            c.compute_bound()
        assert len(children) == n_children
        assert isinstance(children[0], Problem)
        assert children[0].lb == ref_value + 1
        assert children[1].lb == ref_value + 2

    @staticmethod
    def test_copy() -> None:
        """Test copying functionality of Problem."""
        ref_value = 15
        prob = MyProblem(lb_value=ref_value)
        prob.compute_bound()
        shallow_copy = prob.copy(deep=False)
        deep_copy = prob.copy(deep=True)

        assert shallow_copy.lb == ref_value
        assert deep_copy.lb == ref_value
        assert shallow_copy is not prob
        assert deep_copy is not prob
        assert shallow_copy.solution is prob.solution
        assert deep_copy.solution is not prob.solution
