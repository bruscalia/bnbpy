import copy

from bnbprob.slpfssp.job import Job
from bnbprob.slpfssp.permutation import Permutation
from bnbpy.solution import Solution
from bnbpy.status import OptStatus

LARGE_INT = 10000000


class FlowSolution(Solution):
    perm: Permutation

    def __init__(self, perm: Permutation):
        super().__init__()
        self.perm = perm
        self.cost = LARGE_INT
        self.lb = 0.0

    def __del__(self) -> None:
        del self.perm

    def __repr__(self) -> str:
        return self._signature

    def __str__(self) -> str:
        return self._signature

    @property
    def _signature(self) -> str:
        return (
            f'Status: {self.status.name} | Cost: {self.cost} | LB: {self.lb}'
        )

    @property
    def sequence(self) -> list[Job]:
        return self.perm.sequence

    @property
    def free_jobs(self) -> list[Job]:
        return self.perm.free_jobs

    @property
    def n_jobs(self) -> int:
        return len(self.sequence)

    def is_feasible(self) -> bool:
        return self.perm.is_feasible()

    def calc_lb_1m(self) -> int:
        return self.perm.calc_lb_1m()

    def calc_lb_2m(self) -> int:
        return self.perm.calc_lb_2m()

    def lower_bound_1m(self) -> int:
        return self.perm.lower_bound_1m()

    def lower_bound_2m(self) -> int:
        raise NotImplementedError(
            'Use lower_bound_2m() for 2-machine lower bound'
        )
        # return self.perm.lower_bound_2m()
        return 1

    def push_job(self, j: int) -> None:
        self.perm.push_job(j)

    def copy(self, deep: bool = False) -> 'FlowSolution':
        if deep:
            return copy.deepcopy(self)
        sol = FlowSolution.__new__(FlowSolution)
        sol.perm = self.perm.copy()
        sol.cost = LARGE_INT
        sol.lb = 0
        sol.status = OptStatus.NO_SOLUTION
        return sol
