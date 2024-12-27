# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp.vector cimport vector

from bnbprob.pfssp.cython.job cimport Job


cdef class Sigma:

    def __init__(self, list[Job] jobs, vector[int] C):
        self.jobs = jobs
        self.C = C
        self.m = len(self.C)

    def __del__(self):
        self.cleanup()

    cpdef void cleanup(Sigma self):
        cdef:
            Job job

        for job in self.jobs:
            del job
        del self.jobs
        self.jobs = None

    cdef void job_to_bottom(Sigma self, Job job):
        cdef:
            int k

        self.jobs.append(job)
        # Update
        self.C[0] = max(self.C[0], job.r[0]) + job.p[0]
        for k in range(1, self.m):
            self.C[k] = max(self.C[k], self.C[k - 1]) + job.p[k]

    cdef void job_to_top(Sigma self, Job job):
        cdef:
            int k, m

        self.jobs.insert(0, job)
        # Update
        m = self.m - 1

        if m == -1:
            return

        self.C[m] = max(self.C[m], job.q[m]) + job.p[m]

        if m == 0:
            return

        for k in range(1, m + 1):
            self.C[m - k] = max(self.C[m - k], self.C[m - k + 1]) + job.p[m - k]

    cdef Sigma copy(Sigma self):
        cdef:
            Sigma sigma
        sigma = Sigma.__new__(Sigma)
        sigma.jobs = self.jobs.copy()
        sigma.C = vector[int](self.C)
        sigma.m = self.m
        return sigma


cdef Sigma empty_sigma(int m):
    cdef:
        Sigma sigma
    sigma = Sigma.__new__(Sigma)
    sigma.jobs = []
    sigma.C = vector[int](m, 0)
    sigma.m = m
    return sigma
