import copy
from typing import Union

from bnbpy.pypure.status import OptStatus


class Solution:
    """Abstraction for a solution representation"""

    cost: Union[int, float]
    lb: Union[int, float]
    status: OptStatus

    def __init__(self) -> None:
        self.cost = float('inf')  # HUGE_VAL equivalent
        self.lb = -float('inf')  # -HUGE_VAL equivalent
        self.status = OptStatus.NO_SOLUTION

    def __repr__(self) -> str:
        return self._signature

    def __str__(self) -> str:
        return self._signature

    @property
    def _signature(self) -> str:
        return (
            f'Status: {self.status.name} | Cost: {self.cost} | LB: {self.lb}'
        )

    def set_optimal(self) -> None:
        self.status = OptStatus.OPTIMAL

    def set_lb(self, lb: Union[int, float]) -> None:
        self.lb = lb
        if self.status == OptStatus.NO_SOLUTION:
            self.status = OptStatus.RELAXATION

    def set_feasible(self) -> None:
        self.status = OptStatus.FEASIBLE
        self.cost = self.lb

    def set_infeasible(self) -> None:
        self.status = OptStatus.INFEASIBLE
        self.cost = float('inf')

    def fathom(self) -> None:
        self.status = OptStatus.FATHOM
        self.cost = float('inf')

    def copy(self, deep: bool = True) -> 'Solution':
        if deep:
            return copy.deepcopy(self)
        return self._copy()

    def _copy(self) -> 'Solution':
        """Internal shallow copy method matching Cython implementation"""
        other = Solution.__new__(Solution)
        other.cost = self.cost
        other.lb = self.lb
        other.status = self.status
        return other
