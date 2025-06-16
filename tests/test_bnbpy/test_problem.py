import pytest
from fixtures.myproblem import MyProblem
from fixtures.pyproblem import PyProblem

from bnbpy.problem import Problem
from bnbpy.pypure.problem import Problem as PyProblemI
from bnbpy.pypure.solution import Solution as PySolution
from bnbpy.solution import Solution


@pytest.mark.problem
class TestProblem:
    @staticmethod
    def test_problem_initial_state() -> None:
        """Test that the initial state of Problem is correctly set."""
        prob = MyProblem()
        assert isinstance(prob.solution, Solution)
        assert prob.lb == -float('inf')

    @staticmethod
    def test_problem_initial_state_py() -> None:
        """Test that the initial state of PyProblem is correctly set."""
        prob = PyProblem()
        assert isinstance(prob.solution, PySolution)
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
        assert my_problem.solution.status.name == 'RELAXATION'

    @staticmethod
    def test_compute_bound_py(py_problem: PyProblem) -> None:
        """
        Test that compute_bound correctly calculates and sets the lower bound
        for a PyProblem instance.
        """
        ref_value = 10
        py_problem.compute_bound()
        assert py_problem.lb == ref_value
        assert py_problem.solution.lb == ref_value
        assert py_problem.solution.status.name == 'RELAXATION'

    @staticmethod
    def test_check_feasible(my_problem: MyProblem) -> None:
        """
        Test that check_feasible sets the correct status based on feasibility.
        """
        assert my_problem.check_feasible() is True
        assert my_problem.solution.status.name == 'FEASIBLE'

        prob = MyProblem(feasible=False)
        assert prob.check_feasible() is False
        assert prob.solution.status.name == 'INFEASIBLE'

    @staticmethod
    def test_check_feasible_py(py_problem: PyProblem) -> None:
        """
        Test that check_feasible sets the correct status based on feasibility
        for a PyProblem instance.
        """
        assert py_problem.check_feasible() is True
        assert py_problem.solution.status.name == 'FEASIBLE'

        prob = PyProblem(feasible=False)
        assert prob.check_feasible() is False
        assert prob.solution.status.name == 'INFEASIBLE'

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
    def test_branch_on_py() -> None:
        """Test that branch returns child problems for PyProblem."""
        ref_value = 5
        n_children = 2
        prob = PyProblem(lb_value=ref_value)
        children = prob.branch()
        if children is None:
            raise ValueError(
                'Branching returned None, expected child problems.'
            )
        for c in children:
            c.compute_bound()
        assert len(children) == n_children
        assert isinstance(children[0], PyProblemI)
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

    @staticmethod
    def test_copy_py() -> None:
        """Test copying functionality of PyProblem."""
        ref_value = 15
        prob = PyProblem(lb_value=ref_value)
        prob.compute_bound()
        shallow_copy = prob.copy(deep=False)
        deep_copy = prob.copy(deep=True)

        assert shallow_copy.lb == ref_value
        assert deep_copy.lb == ref_value
        assert shallow_copy is not prob
        assert deep_copy is not prob
        assert shallow_copy.solution is prob.solution
        assert deep_copy.solution is not prob.solution
