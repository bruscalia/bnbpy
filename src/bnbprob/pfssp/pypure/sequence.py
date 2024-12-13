import copy
from typing import List, Optional

from bnbprob.pfssp.pypure.job import Job


class BaseSequence:
    def __init__(
        self, jobs: Optional[List[Job]] = None, C: Optional[List[int]] = None
    ):
        if jobs is None:
            jobs = []
        self.jobs = jobs
        self.C = C

    def copy(self, deep=False):
        if deep:
            return copy.deepcopy(self)
        return type(self)(jobs=copy.copy(self.jobs), C=copy.copy(self.C))


class Sigma1(BaseSequence):
    def add_job(self, job: Job):
        self.jobs.append(job)
        self._update_values(job)

    def _update_values(self, job: Job):
        self.C[0] = max(self.C[0], job.r[0]) + job.p[0]
        for k in range(1, len(self.C)):
            self.C[k] = max(self.C[k], self.C[k - 1]) + job.p[k]


class Sigma2(BaseSequence):
    def add_job(self, job: Job):
        self.jobs.insert(0, job)
        self._update_values(job)

    def _update_values(self, job: Job):
        self.C[-1] = max(self.C[-1], job.q[-1]) + job.p[-1]
        for k in range(2, len(self.C) + 1):
            self.C[-k] = max(self.C[-k], self.C[1 - k]) + job.p[-k]
