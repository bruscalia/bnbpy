import copy
from typing import Union

from bnbpy.pypure.status import OptStatus

LOW_NEG = -float('inf')


class Solution:
    """Abstraction for a solution representation"""

    cost: Union[int, float]
    lb: Union[int, float]
    status: OptStatus

    def __init__(self, lb: float = LOW_NEG) -> None:
        self.cost = float('inf')
        self.lb = lb
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

    def get_status_cls(self) -> type:
        return self.status.__class__

    def get_status_options(self) -> dict[str, int]:
        status_cls: type[OptStatus] = self.get_status_cls()
        return {status.name: status.value for status in status_cls}

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
            return self.deep_copy()
        return self.shallow_copy()

    def deep_copy(self) -> 'Solution':
        other = copy.deepcopy(self)
        return other

    def shallow_copy(self) -> 'Solution':
        other = copy.copy(self)
        return other
