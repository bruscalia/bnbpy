# distutils: language = c++
# cython: language_level=3, boundscheck=True, wraparound=True, cdivision=True

from libcpp cimport bool
from libcpp.vector cimport vector

from bnbprob.pfssp.cython.job cimport Job
from bnbprob.pfssp.cython.sequence cimport Sigma1, Sigma2

import copy
from typing import List, Optional, Tuple

from bnbpy import Solution


cdef:
    int LARGE_INT = 10000000


cdef class CyPermutation:

    cdef public:
        int m, level
        list[Job] free_jobs
        Sigma1 sigma1
        Sigma2 sigma2

    def __init__(
        self,
        int m,
        list[Job] free_jobs,
        Sigma1 sigma1,
        Sigma2 sigma2,
        int level = 0,
    ):
        self.m = m
        self.free_jobs = free_jobs
        self.sigma1 = sigma1
        self.sigma2 = sigma2
        self.level = level

    @property
    def sequence(self) -> List[Job]:
        """Sequence of jobs in current solution"""
        return self.sigma1.jobs + self.free_jobs + self.sigma2.jobs

    @property
    def n_jobs(self):
        return len(self.sequence)

    cpdef int calc_bound(CyPermutation self):
        return self.calc_lb_2m()

    cpdef bool is_feasible(CyPermutation self):
        cdef:
            bool valid
        valid = len(self.free_jobs) == 0
        if valid:
            self.compute_starts()
        return valid

    cpdef void push_job(CyPermutation self, int j):
        cdef:
            Job job

        job = self.free_jobs.pop(j)
        if self.level % 2 == 0:
            self.sigma1.add_job(job)
            self.front_updates()
        else:
            self.sigma2.add_job(job)
            self.back_updates()
        self.level += 1

    cpdef void update_params(CyPermutation self):
        self.front_updates()
        self.back_updates()

    cpdef void front_updates(CyPermutation self):
        cdef:
            Job j
            int k
        for j in self.free_jobs:
            j.r[0] = self.sigma1.C[0]
            for k in range(1, self.m):
                j.r[k] = max(self.sigma1.C[k], j.r[k - 1] + j.p[k - 1])

    cpdef void back_updates(CyPermutation self):
        cdef:
            Job j
            int k, m
        m = self.m - 1
        for j in self.free_jobs:
            j.q[m] = self.sigma2.C[m]
            for k in range(1, m + 1):
                j.q[m - k] = max(self.sigma2.C[m - k], j.q[m - k + 1] + j.p[m - k + 1])

    def write(self):
        return '\n'.join([f'Job: {job.j}' for job in self.sequence])

    cpdef int calc_lb_1m(CyPermutation self):
        """Computes lower bounds using 1M relaxation"""
        # All positions are filled take values from self
        if len(self.free_jobs) == 0:
            return self.calc_lb_full()
        # Otherwise, use usual LB1
        return self.lower_bound_1m()

    cpdef int calc_lb_2m(CyPermutation self):
        """Computes lower bounds using 2M + 1M relaxations"""
        cdef:
            int lb1, lb5
        # All positions are filled take values from self
        if len(self.free_jobs) == 0:
            return self.calc_lb_full()
        # Use the greater between 1 and 2 machines
        lb1 = self.lower_bound_1m()
        lb5 = self.lower_bound_2m()
        return max(lb1, lb5)

    cpdef int calc_lb_full(CyPermutation self):
        """Computes lower bounds for when there are no free jobs"""
        cdef:
            int k, cost
        # All positions are filled take values from self
        cost = self.sigma1.C[0] + self.sigma2.C[0]
        for k in range(self.m):
            cost = max(cost, self.sigma1.C[k] + self.sigma2.C[k])
        return cost

    cpdef void compute_starts(CyPermutation self):
        """
        Given a current sequence re-compute attributes release time `r`
        for each job on each machine
        """
        cdef:
            int m, j
            list[Job] seq
            Job job, other

        seq = self.sequence
        for job in seq:
            job.r = vector[int](m, 0)

        job = seq[0]
        job.r[0] = 0
        for m in range(1, self.m):
            job.r[m] = job.r[m - 1] + job.p[m - 1]

        j = 0
        for job in seq[1:]:
            other = seq[j]
            job.r[0] = other.r[0] + other.p[0]
            for m in range(1, self.m):
                job.r[m] = max(
                    job.r[m - 1] + job.p[m - 1], other.r[m] + other.p[m]
                )
            j += 1

    cpdef int lower_bound_1m(CyPermutation self):
        cdef:
            int k, min_r, min_q, sum_p, max_value, temp_value
            Job job

        max_value = 0

        for k in range(self.m):
            min_r = LARGE_INT
            min_q = LARGE_INT
            sum_p = 0

            for job in self.free_jobs:
                if job.r[k] < min_r:
                    min_r = job.r[k]
                if job.q[k] < min_q:
                    min_q = job.q[k]
                sum_p += job.p[k]

            temp_value = min_r + sum_p + min_q
            if temp_value > max_value:
                max_value = temp_value

        return max_value

    cpdef int lower_bound_2m(CyPermutation self):
        cdef:
            int m1, m2, lbs, temp_value
            vector[int] r, q

        lbs = 0
        r = self.get_r()
        q = self.get_q()

        for m1 in range(self.m - 1):
            for m2 in range(m1 + 1, self.m):
                temp_value = (
                    r[m1]
                    + two_mach_problem(self.free_jobs, m1, m2)
                    + q[m2]
                )
                if temp_value > lbs:
                    lbs = temp_value

        return lbs

    cdef vector[int] get_r(self):
        cdef:
            int m, min_rm
            vector[int] r
            Job j

        r = vector[int]()
        for m in range(self.m):
            min_rm = LARGE_INT
            for j in self.free_jobs:
                if j.r[m] < min_rm:
                    min_rm = j.r[m]
            r.push_back(min_rm)

        return r

    cdef vector[int] get_q(self):
        cdef:
            int m, min_qm
            vector[int] q
            Job j

        q = vector[int]()
        for m in range(self.m):
            min_qm = LARGE_INT
            for j in self.free_jobs:
                if j.q[m] < min_qm:
                    min_qm = j.q[m]
            q.push_back(min_qm)

        return q

    def pyget_r(self):
        return list(self.get_r())

    def pyget_q(self):
        return list(self.get_q())

    cpdef CyPermutation copy(CyPermutation self):
        cdef:
            Job j
            list[Job] free_jobs
            CyPermutation other

        free_jobs = [j.copy() for j in self.free_jobs]
        other = CyPermutation(
            self.m,
            free_jobs,
            self.sigma1.copy(),
            self.sigma2.copy(),
            self.level,
        )
        return other


cdef int two_mach_problem(list[Job] jobs, int m1, int m2):
    cdef:
        Job job
        list[tuple[Job, int, int]] job_times, j1, j2, opt

    job_times = [
        (job, job.p[m1] + job.lat[m2][m1], job.p[m2] + job.lat[m2][m1])
        for job in jobs
    ]
    # Separate jobs into two sets based on t1 and t2
    j1 = [x for x in job_times if x[1] <= x[2]]
    j2 = [x for x in job_times if x[1] > x[2]]

    # Sort set1 in ascending order of t1
    j1.sort(key=_get_1, reverse=False)

    # Sort set2 in descending order of t2
    j2.sort(key=_get_2, reverse=True)

    # Concatenate the sorted lists
    opt = j1 + j2

    return two_mach_makespan(opt, m1, m2)


cpdef int _get_1(tuple[Job, int, int] x):
    return x[1]


cpdef int _get_2(tuple[Job, int, int] x):
    return x[2]


cdef int two_mach_makespan(
    List[Tuple[Job, int, int]] job_times,
    int m1,
    int m2
):
    cdef:
        int time_m1, time_m2, _
        Job job

    time_m1 = 0  # Completion time for machine 1
    time_m2 = 0  # Completion time for machine 2

    for job, _, _ in job_times:
        # Machine 1 processes each job sequentially
        time_m1 += job.p[m1]

        # Machine 2 starts after the job is done
        # on Machine 1 and any lag is considered
        time_m2 = max(time_m1 + job.lat[m2][m1], time_m2) + job.p[m2]

    return max(time_m1, time_m2)
