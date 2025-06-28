from typing import Optional, Union

from bnbpy.cython.status import OptStatus

LOW_NEG = -float('inf')

class Solution:
    """Abstraction for a solution representation"""

    cost: Optional[Union[int, float]]
    lb: Union[int, float]
    status: OptStatus

    def __init__(self) -> None:
        ...

    @property
    def _signature(self) -> str:
        ...

    def set_optimal(self) -> None:
        ...

    def set_lb(self, lb: Union[int, float]) -> None:
        ...

    def set_feasible(self) -> None:
        ...

    def set_infeasible(self) -> None:
        ...

    def fathom(self) -> None:
        ...

    def copy(self, deep: bool = True) -> 'Solution':
        ...
