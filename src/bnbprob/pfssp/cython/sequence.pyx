# distutils: language = c++
# cython: language_level=3, boundscheck=True, wraparound=True, cdivision=True

from libcpp.vector cimport vector

from bnbprob.pfssp.cython.job cimport Job

from typing import List


cdef class Sigma1:

    def __init__(
        self, list[Job] jobs, vector[int] C
    ):
        self.jobs = jobs
        self.C = C

    cdef void add_job(Sigma1 self, Job job):
        self.jobs.append(job)
        self._update_values(job)

    cdef Sigma1 copy(Sigma1 self):
        cdef:
            Job j
            list[Job] new_jobs
        new_jobs = [j for j in self.jobs]
        return Sigma1(new_jobs, vector[int](self.C))

    cdef void _update_values(Sigma1 self, Job job):
        cdef:
            int k, m

        m = <int>self.C.size()
        self.C[0] = max(self.C[0], job.r[0]) + job.p[0]
        for k in range(1, m):
            self.C[k] = max(self.C[k], self.C[k - 1]) + job.p[k]

    def pycopy(self):
        return self.copy()

    def pyadd_job(self, job: Job):
        self.add_job(job)

    def get_jobs(self) -> list[Job]:
        return [j for j in self.jobs]

    def get_C(self) -> list[int]:
        return [c for c in self.C]


cdef class Sigma2:

    def __init__(
        self, list[Job] jobs, vector[int] C
    ):
        self.jobs = jobs
        self.C = C

    cdef void add_job(Sigma2 self, Job job):
        self.jobs.insert(0, job)
        self._update_values(job)

    cdef Sigma2 copy(Sigma2 self):
        cdef:
            Job j
            list[Job] new_jobs
        new_jobs = [j for j in self.jobs]
        return Sigma2(new_jobs, vector[int](self.C))

    cdef void _update_values(Sigma2 self, Job job):
        cdef:
            int k, m

        m = <int>self.C.size() - 1

        if m == -1:
            return

        self.C[m] = max(self.C[m], job.q[m]) + job.p[m]

        if m == 0:
            return

        for k in range(1, m + 1):
            self.C[m - k] = max(self.C[m - k], self.C[m - k + 1]) + job.p[m - k]

    def pycopy(self):
        return self.copy()

    def pyadd_job(self, job: Job):
        self.add_job(job)

    def get_jobs(self) -> list[Job]:
        return [j for j in self.jobs]

    def get_C(self) -> list[int]:
        return [c for c in self.C]
