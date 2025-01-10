# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp.vector cimport vector

from bnbprob.pfssp.cython.job cimport Job, PyJob

ctypedef Job* JobPtr


cdef void job_to_bottom(Sigma& sigma, Job* job):
    cdef:
        int k

    sigma.jobs.push_back(job)
    # Update
    sigma.C[0] = max(sigma.C[0], job.r[0]) + job.p[0]
    for k in range(1, sigma.m):
        sigma.C[k] = max(sigma.C[k], sigma.C[k - 1]) + job.p[k]


cdef void job_to_top(Sigma& sigma, Job* job):
    cdef:
        int k, m

    sigma.jobs.insert(sigma.jobs.begin(), job)
    # Update
    m = sigma.m - 1

    if m == -1:
        return

    sigma.C[m] = max(sigma.C[m], job.q[m]) + job.p[m]

    if m == 0:
        return

    for k in range(1, m + 1):
        sigma.C[m - k] = max(sigma.C[m - k], sigma.C[m - k + 1]) + job.p[m - k]


cdef Sigma empty_sigma(int m):
    cdef:
        Sigma sigma
    sigma = Sigma(
        vector[JobPtr](),
        vector[int](m, 0),
        m
    )
    return sigma


cdef class PySigma:

    def __init__(self, m: int):
        self.sigma = empty_sigma(m)

    cpdef list[PyJob] get_jobs(PySigma self):
        cdef:
            int i
            PyJob job
            list[PyJob] out

        out = []
        for i in range(self.sigma.jobs.size()):
            job = PyJob.__new__(PyJob)
            job.job = self.sigma.jobs[i][0]
            out.append(job)
        return out

    cpdef vector[int] get_C(PySigma self):
        return self.sigma.C

    cpdef void job_to_bottom(PySigma self, PyJob job):
        job_to_bottom(self.sigma, &job.job)

    cpdef void job_to_top(PySigma self, PyJob job):
        job_to_top(self.sigma, &job.job)
