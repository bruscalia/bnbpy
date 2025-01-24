from typing import Optional, Union

from bnbpy.pypure.status import OptStatus

LOW_NEG = -float('inf')

class Solution:
    """Abstraction for a solution representation"""

    cost: Optional[Union[int, float]]
    lb: Union[int, float]
    status: OptStatus

    def __init__(self, lb=LOW_NEG):
        ...

    @property
    def _signature(self):
        ...

    def set_optimal(self):
        ...

    def set_lb(self, lb: Union[int, float]):
        ...

    def set_feasible(self):
        ...

    def set_infeasible(self):
        ...

    def fathom(self):
        ...

    def copy(self, deep=True):
        ...
