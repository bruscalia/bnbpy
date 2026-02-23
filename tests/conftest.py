import pytest
from myfixtures.myproblem import MyProblem


@pytest.fixture
def my_problem() -> MyProblem:
    return MyProblem(lb_value=10, feasible=True)
