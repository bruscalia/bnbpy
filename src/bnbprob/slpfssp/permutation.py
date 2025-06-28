import copy
from dataclasses import dataclass

from bnbprob.slpfssp.job import Job
from bnbprob.slpfssp.sigma import Sigma

LARGE_INT = 10000000


class Permutation:  # noqa: PLR0904
    m: list[int]
    """Number of machines on each parallel semiline"""
    free_jobs: list[Job]
    """Jobs that are not yet in the sequence"""
    sigma1: Sigma
    """First part of the sequence (bottom)"""
    sigma2: Sigma
    """Second part of the sequence (top)"""
    level: int
    """Level of the permutation in the search tree,
    even for bottom, odd for top"""

    def __init__(
        self,
        m: list[int],
        free_jobs: list[Job],
        sigma1: Sigma,
        sigma2: Sigma,
        level: int = 0,
    ):
        self.m = m
        self.free_jobs = free_jobs
        self.sigma1 = sigma1
        self.sigma2 = sigma2
        self.level = level
        self.update_params()

    def __del__(self) -> None:
        self.cleanup()

    def cleanup(self) -> None:
        del self.free_jobs
        del self.sigma1
        del self.sigma2

    @staticmethod
    def from_p(p: list[list[list[int]]]) -> 'Permutation':
        """Creates a permutation from the list of processing times
        for each job on each parallel semiline and each machine.

        Parameters
        ----------
        p : list[list[list[int]]]
            Processing times

        Returns
        -------
        Permutation
            Solution representation
        """
        m = [len(pi) for pi in p[0]]
        jobs = [Job(j, p[j]) for j in range(len(p))]
        return start_perm(m, jobs)

    @property
    def sequence(self) -> list[Job]:
        """Sequence of jobs in current solution"""
        return self.get_sequence()

    @property
    def n_jobs(self) -> int:
        return (
            len(self.sigma1.jobs) + len(self.free_jobs) + len(self.sigma2.jobs)
        )

    @property
    def n_free(self) -> int:
        return len(self.free_jobs)

    def get_sequence(self) -> list[Job]:
        return self.sigma1.jobs + self.free_jobs + self.sigma2.jobs

    def get_sequence_copy(self) -> list[Job]:
        seq = self.get_sequence()
        return [job.copy() for job in seq]

    def calc_bound(self) -> int:
        return self.calc_lb_2m()

    def is_feasible(self) -> bool:
        valid = len(self.free_jobs) == 0
        if valid:
            self.compute_starts()
        return valid

    def push_job(self, j: int) -> None:
        job = self.free_jobs.pop(j)
        if self.level % 2 == 0:
            self.sigma1.job_to_bottom(job)
            self.front_updates()
        else:
            self.sigma2.job_to_top(job)
            self.back_updates()
        self.level += 1

    def update_params(self) -> None:
        self.front_updates()
        self.back_updates()

    def front_updates(self) -> None:
        for job in self.free_jobs:
            job_rec = 0
            for sl, m_sl in enumerate(self.m):
                job.r[sl][0] = self.sigma1.C[sl][0]
                for k in range(1, m_sl - job.s):
                    job.r[sl][k] = max(
                        self.sigma1.C[sl][k],
                        job.r[sl][k - 1] + job.p[sl][k - 1],
                    )
                job_rec = max(job_rec, job.r[sl][k] + job.p[sl][k])
            for sl, m_sl in enumerate(self.m):
                job.r[sl][-job.s] = max(self.sigma1.C[sl][-job.s], job_rec)
                for k in range(m_sl - job.s + 1, m_sl):
                    job.r[sl][k] = max(
                        self.sigma1.C[sl][k],
                        job.r[sl][k - 1] + job.p[sl][k - 1],
                    )

    def back_updates(self) -> None:
        for job in self.free_jobs:
            job_rec = 0
            for sl, m_sl in enumerate(self.m):
                m_ = m_sl - 1
                job.q[sl][m_] = self.sigma2.C[sl][m_]
                for k in range(1, job.s):
                    job.q[sl][m_ - k] = max(
                        self.sigma2.C[sl][m_ - k],
                        job.q[sl][m_ - k + 1] + job.p[sl][m_ - k + 1],
                    )
                job_rec = max(job_rec, job.q[sl][m_] + job.p[sl][m_])
            for sl, m_sl in enumerate(self.m):
                m_ = m_sl - job.s - 1  # Last machine before reconciliation
                job.q[sl][m_] = max(self.sigma2.C[sl][m_], job_rec)
                for _ in range(1, self.m[sl] - job.s):
                    m_ -= 1
                    job.q[sl][m_] = max(
                        self.sigma2.C[sl][m_],
                        job.q[sl][m_ + 1] + job.p[sl][m_ + 1],
                    )

    def calc_lb_1m(self) -> int:
        # All positions are filled take values from self
        if len(self.free_jobs) == 0:
            return self.calc_lb_full()
        # Otherwise, use usual LB1
        return self.lower_bound_1m()

    def calc_lb_2m(self) -> int:
        # All positions are filled take values from self
        if len(self.free_jobs) == 0:
            return self.calc_lb_full()
        # Use the greater between 1 and 2 machines
        lb1 = self.lower_bound_1m()
        lb5 = self.lower_bound_2m()
        return max(lb1, lb5)

    def calc_lb_full(self) -> int:
        # All positions are filled take values from self
        cost = max(
            self.sigma1.C[sl][k] + self.sigma2.C[sl][k]
            for sl, m_sl in enumerate(self.m)
            for k in range(m_sl)
        )
        return cost

    def compute_starts(self) -> None:
        seq = self.get_sequence()
        for j in range(len(seq)):
            job = seq[j]
            for sl, m_sl in enumerate(self.m):
                job.r[sl] = [0] * m_sl

        job = seq[0]
        self._compute_start_first_job(job)

        for j in range(1, len(seq)):
            job = seq[j]
            prev = seq[j - 1]
            job_rec = 0
            # Update on each semiline
            for sl, m_sl in enumerate(self.m):
                job.r[sl][0] = prev.r[sl][0] + prev.p[sl][0]
                for m_ in range(1, m_sl - job.s):
                    job.r[sl][m_] = max(
                        job.r[sl][m_ - 1] + job.p[sl][m_ - 1],
                        prev.r[sl][m_] + prev.p[sl][m_],
                    )
                job_rec = max(
                    job_rec,
                    job.r[sl][m_] + job.p[sl][m_]
                )
            # Update on reconciliation machine(s)
            for sl, _ in enumerate(self.m):
                job_rec = max(
                    job_rec, prev.r[sl][-job.s] + prev.p[sl][-job.s]
                )
            for sl, m_sl in enumerate(self.m):
                job.r[sl][-job.s] = job_rec
                for m_ in range(m_sl - job.s + 1, m_sl):
                    job.r[sl][m_] = max(
                        job.r[sl][m_ - 1] + job.p[sl][m_ - 1],
                        prev.r[sl][m_] + prev.p[sl][m_],
                    )

    def _compute_start_first_job(self, job: Job) -> None:
        job_rec = 0
        # Update the first job on each semiline
        for sl, m_sl in enumerate(self.m):
            for m_ in range(1, m_sl - job.s):
                job.r[sl][m_] = job.r[sl][m_ - 1] + job.p[sl][m_ - 1]
            job_rec = max(job_rec, job.r[sl][m_] + job.p[sl][m_])
        # Update the first job on the reconciliation machine(s)
        for sl, m_sl in enumerate(self.m):
            job.r[sl][-job.s] = job_rec
            for m_ in range(m_sl - job.s + 1, m_sl):
                job.r[sl][m_] = job.r[sl][m_ - 1] + job.p[sl][m_ - 1]

    def lower_bound_1m(self) -> int:
        return max(
            min(job.r[sl][k] for job in self.free_jobs)
            + sum(job.p[sl][k] for job in self.free_jobs)
            + min(job.q[sl][k] for job in self.free_jobs)
            for sl, m_sl in enumerate(self.m)
            for k in range(m_sl)
        )

    def lower_bound_2m(self) -> int:
        r = self.get_r()
        q = self.get_q()

        return max(
            r[sl][m1]
            + two_mach_problem(self.free_jobs, sl, m1, m2)
            + q[sl][m2]
            for sl, m_sl in enumerate(self.m)
            for m1 in range(m_sl - 1)
            for m2 in range(m1 + 1, m_sl)
        )

    def get_r(self) -> list[list[int]]:
        return [
            [
                min(job.r[sl][m_] for job in self.free_jobs)
                for m_ in range(m_sl)
            ]
            for sl, m_sl in enumerate(self.m)
        ]

    def get_q(self) -> list[list[int]]:
        return [
            [
                min(job.q[sl][m_] for job in self.free_jobs)
                for m_ in range(m_sl)
            ]
            for sl, m_sl in enumerate(self.m)
        ]

    def copy(self, deep: bool = False) -> 'Permutation':
        if deep:
            return copy.deepcopy(self)
        perm = Permutation.__new__(Permutation)
        perm.m = self.m
        perm.free_jobs = [job.copy() for job in self.free_jobs]
        perm.sigma1 = self.sigma1.copy()
        perm.sigma2 = self.sigma2.copy()
        perm.level = self.level
        return perm


def start_perm(m: list[int], free_jobs: list[Job]) -> Permutation:
    perm = Permutation.__new__(Permutation)
    perm.m = m
    perm.free_jobs = free_jobs
    perm.sigma1 = Sigma.empty_sigma(m)
    perm.sigma2 = Sigma.empty_sigma(m)
    perm.level = 0
    perm.update_params()
    return perm


@dataclass
class JobParams:
    t1: int
    t2: int
    p1: int
    p2: int
    lat: int


def two_mach_problem(jobs: list[Job], sl: int, m1: int, m2: int) -> int:
    j1: list[JobParams] = []
    j2: list[JobParams] = []
    all_j = [
        JobParams(
            job.p[sl][m1] + job.lat[sl][m2][m1],
            job.p[sl][m2] + job.lat[sl][m2][m1],
            job.p[sl][m1],
            job.p[sl][m2],
            job.lat[sl][m2][m1],
        )
        for job in jobs
    ]

    j1 = [jparam for jparam in all_j if jparam.t1 <= jparam.t2]
    j2 = [jparam for jparam in all_j if jparam.t2 < jparam.t1]

    # Sort set1 in ascending order of t1
    j1.sort(key=lambda x: x.t1, reverse=False)

    # Sort set2 in descending order of t2
    j2.sort(key=lambda x: x.t2, reverse=True)

    # Include j2 into j1
    j1.extend(j2)

    # Concatenate the sorted lists
    res = two_mach_makespan(j1)
    return res


def two_mach_makespan(job_times: list[JobParams]) -> int:
    time_m1 = 0  # Completion time for machine 1
    time_m2 = 0  # Completion time for machine 2

    for j in range(len(job_times)):
        # Machine 1 processes each job sequentially
        time_m1 += job_times[j].p1

        # Machine 2 starts after the job is done
        # on Machine 1 and any lag is considered
        time_m2 = (
            max(time_m1 + job_times[j].lat, time_m2)
            + job_times[j].p2
        )

    return max(time_m1, time_m2)
