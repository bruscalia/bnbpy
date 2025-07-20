from abc import ABC, abstractmethod
from typing import Generic, TypeVar, final


class Solution:
    pass


S = TypeVar("S", bound=Solution)


class Problem(ABC, Generic[S]):
    solution: S

    # @abstractmethod
    def __init__(self) -> None:
        self.solution: S
        pass


class Algorithm:

    @staticmethod
    def solve(problem: Problem[S]) -> S:
        # Placeholder for the actual solving logic
        return problem.solution


class MySolution(Solution):
    pass


class MyProblem(Problem[MySolution]):

    def __init__(self, solution: MySolution):
        self.solution = solution


DefaultProblem = Problem[Solution]

WrongProblem = Problem[int]


class OtherProblem(DefaultProblem):
    pass


prob = Problem()
problem = MyProblem()
otherproblem = OtherProblem()

sol = Algorithm.solve(problem)
othersol = Algorithm.solve(otherproblem)
