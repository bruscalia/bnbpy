import copy
from typing import List, Optional, Tuple

from bnbprob.pfssp.pypure.job import Job
from bnbprob.pfssp.pypure.sequence import Sigma1, Sigma2
from bnbpy import Solution


class Permutation(Solution):
    level: int
    free_jobs: List[Job]
    sigma1: Sigma1
    sigma2: Sigma2
    cost: Optional[int]

    def __init__(
        self,
        m: int,
        free_jobs: List[Job],
        sigma1: Optional[Sigma1] = None,
        sigma2: Optional[Sigma2] = None,
        level: int = 0,
    ):
        super().__init__()
        self.level = level
        self.m = m
        self.free_jobs = free_jobs
        # Define empty sequences if not defined
        if sigma1 is None:
            sigma1 = Sigma1(C=[0 for _ in range(m)])
        self.sigma1 = sigma1
        if sigma2 is None:
            sigma2 = Sigma2(C=[0 for _ in range(m)])
        self.sigma2 = sigma2
        self.update_params()

    @property
    def sequence(self) -> List[Job]:
        """Sequence of jobs in current solution"""
        return self.sigma1.jobs + self.free_jobs + self.sigma2.jobs

    @property
    def n_jobs(self):
        return len(self.sequence)

    def calc_bound(self):
        return self.calc_lb_2m()

    def is_feasible(self) -> bool:
        valid = len(self.free_jobs) == 0
        if valid:
            self.compute_starts()
        return valid

    def push_job(self, j: int):
        job = self.free_jobs.pop(j)
        if self.level % 2 == 0:
            self.sigma1.add_job(job)
            self.front_updates()
        else:
            self.sigma2.add_job(job)
            self.back_updates()
        self.level += 1

    def update_params(self):
        self.front_updates()
        self.back_updates()

    def front_updates(self):
        for j in self.free_jobs:
            j.r[0] = self.sigma1.C[0]
            for k in range(1, self.m):
                j.r[k] = max(self.sigma1.C[k], j.r[k - 1] + j.p[k - 1])

    def back_updates(self):
        for j in self.free_jobs:
            j.q[-1] = self.sigma2.C[-1]
            for k in range(2, self.m + 1):
                j.q[-k] = max(self.sigma2.C[-k], j.q[1 - k] + j.p[1 - k])

    def write(self):
        return '\n'.join([f'Job: {job.j}' for job in self.sequence])

    def calc_lb_1m(self) -> Optional[int]:
        """Computes lower bounds using 1M relaxation"""
        # All positions are filled take values from self
        if len(self.free_jobs) == 0:
            return self.calc_lb_full()
        # Otherwise, use usual LB1
        return self.lower_bound_1m()

    def calc_lb_2m(self) -> Optional[int]:
        """Computes lower bounds using 2M + 1M relaxations"""
        # All positions are filled take values from self
        if len(self.free_jobs) == 0:
            return self.calc_lb_full()
        # Use the greater between 1 and 2 machines
        lb1 = self.lower_bound_1m()
        lb5 = self.lower_bound_2m()
        return max(lb1, lb5)

    def calc_lb_full(self) -> Optional[int]:
        """Computes lower bounds for when there are no free jobs"""
        # All positions are filled take values from self
        return max(self.sigma1.C[k] + self.sigma2.C[k] for k in range(self.m))

    def compute_starts(self):
        """
        Given a current sequence re-compute attributes release time `r`
        for each job on each machine
        """
        seq = self.sequence
        for job in seq:
            job.r = [0 for _ in range(self.m)]

        job = seq[0]
        job.r[0] = 0
        for m in range(1, self.m):
            job.r[m] = job.r[m - 1] + job.p[m - 1]

        for j, job in enumerate(seq[1:]):
            job.r[0] = seq[j].r[0] + seq[j].p[0]
            for m in range(1, self.m):
                job.r[m] = max(
                    job.r[m - 1] + job.p[m - 1], seq[j].r[m] + seq[j].p[m]
                )

    def lower_bound_1m(self):
        return max(
            min(job.r[k] for job in self.free_jobs)
            + sum(job.p[k] for job in self.free_jobs)
            + min(job.q[k] for job in self.free_jobs)
            for k in range(self.m)
        )

    def lower_bound_2m(self):
        lbs = max(
            self.r(m1)
            + two_mach_problem(self.free_jobs, m1, m2)
            + self.q(m2)
            for m1 in range(self.m - 1)
            for m2 in range(m1 + 1, self.m)
        )
        return lbs

    def r(self, m: int):
        return min(j.r[m] for j in self.free_jobs)

    def q(self, m: int):
        return min(j.q[m] for j in self.free_jobs)

    def copy(self, deep=False):
        if deep:
            return copy.deepcopy(self)
        other = Permutation(
            self.m,
            [j.copy(deep=False) for j in self.free_jobs],
            self.sigma1.copy(deep=False),
            self.sigma2.copy(deep=False),
            self.level,
        )
        return other


def two_mach_problem(jobs: List[Job], m1: int, m2: int) -> int:
    job_times = [
        (job, job.p[m1] + job.lat[m2][m1], job.p[m2] + job.lat[m2][m1])
        for job in jobs
    ]
    # Separate jobs into two sets based on t1 and t2
    j1 = [x for x in job_times if x[1] <= x[2]]
    j2 = [x for x in job_times if x[1] > x[2]]

    # Sort set1 in ascending order of t1
    j1.sort(key=lambda x: x[1], reverse=False)

    # Sort set2 in descending order of t2
    j2.sort(key=lambda x: x[2], reverse=True)

    # Concatenate the sorted lists
    opt = j1 + j2

    return two_mach_makespan(opt, m1, m2)


def two_mach_makespan(job_times: List[Tuple[Job, int, int]], m1: int, m2: int):
    time_m1 = 0  # Completion time for machine 1
    time_m2 = 0  # Completion time for machine 2

    for job, _, _ in job_times:
        # Machine 1 processes each job sequentially
        time_m1 += job.p[m1]

        # Machine 2 starts after the job is done
        # on Machine 1 and any lag is considered
        time_m2 = max(time_m1 + job.lat[m2][m1], time_m2) + job.p[m2]

    return max(time_m1, time_m2)
