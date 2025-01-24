import copy
from typing import Optional, Union

from bnbpy.pypure.status import OptStatus

LOW_NEG = -float('inf')


class Solution:
    """Abstraction for a solution representation"""

    cost: Union[int, float]
    lb: Union[int, float]
    status: OptStatus

    def __init__(self, lb=LOW_NEG):
        self.cost = float('inf')
        self.lb = lb
        self.status = OptStatus.NO_SOLUTION

    def __repr__(self) -> str:
        return self._signature

    def __str__(self) -> str:
        return self._signature

    @property
    def _signature(self):
        return (
            f'Status: {self.status.name} | Cost: {self.cost} | LB: {self.lb}'
        )

    def get_status_cls(self):
        return self.status.__class__

    def get_status_options(self):
        status_cls = self.get_status_cls()
        return {status.name: status.value for status in status_cls}

    def set_optimal(self):
        self.status = OptStatus.OPTIMAL

    def set_lb(self, lb: Union[int, float]):
        self.lb = lb
        if self.status == OptStatus.NO_SOLUTION:
            self.status = OptStatus.RELAXATION

    def set_feasible(self):
        self.status = OptStatus.FEASIBLE
        self.cost = self.lb

    def set_infeasible(self):
        self.status = OptStatus.INFEASIBLE
        self.cost = float('inf')

    def fathom(self):
        self.status = OptStatus.FATHOM
        self.cost = float('inf')

    def copy(self, deep=True):
        if deep:
            return self.deep_copy()
        return self.shallow_copy()

    def deep_copy(self):
        other = copy.deepcopy(self)
        return other

    def shallow_copy(self):
        other = copy.copy(self)
        return other
