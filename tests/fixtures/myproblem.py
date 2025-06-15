from typing import List, Optional, Union

import pytest

from bnbpy.cython.problem import Problem


class MyProblem(Problem):
    """Concrete subclass of Problem for testing purposes."""

    def __init__(
        self,
        lb_value: Optional[Union[int, float]] = None,
        feasible: bool = True,
    ):
        super().__init__()
        self._lb_value = lb_value
        self._feasible = feasible

    def calc_bound(self) -> Optional[Union[int, float]]:
        return self._lb_value

    def is_feasible(self) -> bool:
        return self._feasible

    def branch(self) -> Optional[List['Problem']]:
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
