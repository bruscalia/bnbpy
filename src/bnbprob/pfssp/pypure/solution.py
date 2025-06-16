import copy

from bnbprob.pfssp.pypure.job import Job
from bnbprob.pfssp.pypure.permutation import Permutation
from bnbpy.pypure.solution import Solution
from bnbpy.pypure.status import OptStatus

LARGE_INT = 10000000


class FlowSolution(Solution):
    perm: Permutation

    def __init__(self, perm: Permutation):
        super().__init__(lb=0)
        self.perm = perm
        self.cost = LARGE_INT

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
        return self.perm.lower_bound_1m()

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
