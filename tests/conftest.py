import pytest
from fixtures.myproblem import MyProblem
from fixtures.pyproblem import PyProblem


@pytest.fixture
def my_problem() -> MyProblem:
    return MyProblem(lb_value=10, feasible=True)

@pytest.fixture
def py_problem() -> PyProblem:
    return PyProblem(lb_value=10, feasible=True)
