from typing import List, Optional

from bnbprob.machdeadline.job import Job
from bnbpy import Solution


class MachSolution(Solution):
    sequence: Optional[List[Job]]
    lb: Optional[int]
    cost: Optional[int]

    def __init__(
        self,
        sequence: Optional[List[Job]]
    ):
        super().__init__()
        self.sequence = sequence
        self._set_job_attrs()

    def _set_job_attrs(self):
        for k, job in enumerate(self.sequence):
            job.set_position(k)
            if k == 0:
                job.set_completion(job.p)
            else:
                job.set_completion(self.sequence[k - 1].c + job.p)

    def write(self):
        return "\n".join(
            [f"Job: {job.id} - Completion: {job.c}" for job in self.sequence]
        )

    def calc_bound(self) -> Optional[int]:
        self.lb = sum(job.w * job.c for job in self.sequence)
        return self.lb

    def check_feasible(self) -> bool:
        valid = all(job.feasible for job in self.sequence)
        if valid:
            self.cost = self.lb
        return valid
