
from bnbprob.pfssp.pypure.job import Job
from bnbpy.cython.status import OptStatus

class FlowSolution:
    """
    Solution representation to the Permutation Flow Shop
    Scheduling Problem
    """
    cost: int
    lb: int
    status: OptStatus

    def __del__(self) -> None:
        ...

    def get_status_cls(self) -> type:
        ...

    def get_status_options(self) -> list[str]:
        ...

    @property
    def sequence(self) -> list[Job]:
        ...

    @property
    def free_jobs(self) -> list[Job]:
        ...

    def calc_lb_1m(self) -> int:
        ...

    def calc_lb_2m(self) -> int:
        ...

    def copy(self) -> 'FlowSolution':
        ...
