from typing import List

from bnbprob.machdeadline.job import Job
from bnbpy import Solution

LARGE_POS: int = 10**9


class MachSolution(Solution):
    sequence: List[Job]
    lb: int
    cost: int

    def __init__(self, sequence: List[Job]):
        super().__init__()
        self.sequence = sequence
        self._set_job_attrs()
        self.lb = 0
        self.cost = LARGE_POS

    def _set_job_attrs(self) -> None:
        for k, job in enumerate(self.sequence):
            job.set_position(k)
            if k == 0:
                job.set_completion(job.p)
            else:
                last_c = self.sequence[k - 1].c
                if last_c is None:
                    raise ValueError('Last job completion time is not set.')
                job.set_completion(last_c + job.p)

    def write(self) -> str:
        return '\n'.join([
            f'Job: {job.id} - Completion: {job.c}' for job in self.sequence
        ])

    def calc_bound(self) -> int:
        self.lb = sum(
            job.w * job.c for job in self.sequence if job.c is not None
        )
        return self.lb

    def check_feasible(self) -> bool:
        valid = all(job.feasible for job in self.sequence)
        if valid:
            self.cost = self.lb
        return valid
