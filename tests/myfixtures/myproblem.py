from typing import List, Optional, Union

from bnbpy.cython.problem import Problem


class MyProblem(Problem):
    """Concrete subclass of Problem for testing purposes."""

    def __init__(
        self,
        lb_value: Optional[Union[int, float]] = None,
        feasible: bool = True,
    ):
        super().__init__()
        if lb_value is None:
            lb_value = 0.0
        self._lb_value = lb_value
        self._feasible = feasible

    def calc_bound(self) -> float:
        return float(self._lb_value)

    def is_feasible(self) -> bool:
        return self._feasible

    def branch(self) -> List['Problem']:
        # Create two child problems for testing
        child1 = MyProblem(
            lb_value=self._lb_value + 1 if self._lb_value is not None else 1,
            feasible=True,
        )
        child2 = MyProblem(
            lb_value=self._lb_value + 2 if self._lb_value is not None else 2,
            feasible=False,
        )
        return [child1, child2]


class UnboundedProblem(Problem):
    def calc_bound(_) -> float:
        return float('-inf')

    def is_feasible(_) -> bool:
        return False

    def branch(self) -> List['Problem']:
        return [self.copy(), self.copy()]
