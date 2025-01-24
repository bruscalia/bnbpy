
from bnbprob.pfssp.cython.job import Job
from bnbprob.pfssp.cython.permutation import Permutation
from bnbpy.cython.status import OptStatus

class FlowSolution:
    """
    Solution representation to the Permutation Flow Shop
    Scheduling Problem
    """
    perm: Permutation
    cost: int
    lb: int
    status: OptStatus

    def __init__(self, perm: Permutation):
        ...

    def __del__(self):
        ...

    def get_status_cls(self):
        ...

    def get_status_options(self):
        ...

    @property
    def sequence(self) -> list[Job]:
        ...

    @property
    def free_jobs(self) -> list[Job]:
        return self.perm.free_jobs

    def calc_lb_1m(self) -> int:
        ...

    def calc_lb_2m(self) -> int:
        ...

    def copy(self) -> 'FlowSolution':
        ...
