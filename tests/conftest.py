import pytest
from myfixtures.myproblem import MyProblem
from myfixtures.pyproblem import PyProblem


@pytest.fixture
def my_problem() -> MyProblem:
    return MyProblem(lb_value=10, feasible=True)


@pytest.fixture
def py_problem() -> PyProblem:
    return PyProblem(lb_value=10, feasible=True)
