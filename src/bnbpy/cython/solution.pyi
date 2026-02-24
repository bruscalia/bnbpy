from typing import Union

from bnbpy.cython.status import OptStatus

class Solution:
    """Solution representation"""

    cost: float
    """
    Upper bound of the solution
    (infinity in case of infeasibility or not being solved)
    """

    lb: float
    """Lower bound of the solution"""

    status: OptStatus
    """Optimization status of the solution"""

    def __init__(self) -> None: ...

    def __repr__(self) -> str: ...

    def __str__(self) -> str: ...

    @property
    def _signature(self) -> str: ...

    def set_optimal(self) -> None: ...

    def set_lb(self, lb: Union[int, float]) -> None: ...

    def set_feasible(self) -> None: ...

    def set_infeasible(self) -> None: ...

    def fathom(self) -> None: ...

    def copy(self, deep: bool = True) -> 'Solution': ...
