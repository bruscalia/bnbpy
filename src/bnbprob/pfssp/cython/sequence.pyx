# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True

from libcpp.vector cimport vector

from bnbprob.pfssp.cython.job cimport CyJob


cdef void job_to_bottom(Sigma& sigma, CyJob& job):
    cdef:
        int k, m

    # Push
    sigma.jobs.push_back(job)

    # Update
    m = <int>sigma.C.size()
    sigma.C[0] = max(sigma.C[0], job.r[0]) + job.p[0]
    for k in range(1, m):
        sigma.C[k] = max(sigma.C[k], sigma.C[k - 1]) + job.p[k]


cdef void job_to_top(Sigma& sigma, CyJob& job):
    cdef:
        int k, m

    # Push
    sigma.jobs.insert(sigma.jobs.begin(), job)

    # Update
    m = <int>sigma.C.size() - 1

    if m == -1:
        return

    sigma.C[m] = max(sigma.C[m], job.q[m]) + job.p[m]

    if m == 0:
        return

    for k in range(1, m + 1):
        sigma.C[m - k] = max(sigma.C[m - k], sigma.C[m - k + 1]) + job.p[m - k]


cpdef Sigma copy_sigma(Sigma& sigma):
    return Sigma(vector[CyJob](sigma.jobs), vector[int](sigma.C))


cdef class Sigma1:

    def __init__(
        self, vector[CyJob]& jobs, vector[int] C
    ):
        self.jobs = jobs
        self.C = C

    cdef void add_job(Sigma1 self, CyJob& job):
        self.jobs.push_back(job)
        self._update_values(job)

    cpdef Sigma1 copy(Sigma1 self):
        return Sigma1(vector[CyJob](self.jobs), vector[int](self.C))

    cdef void _update_values(Sigma1 self, CyJob& job):
        cdef:
            int k, m

        m = <int>self.C.size()
        self.C[0] = max(self.C[0], job.r[0]) + job.p[0]
        for k in range(1, m):
            self.C[k] = max(self.C[k], self.C[k - 1]) + job.p[k]


cdef class Sigma2:

    def __init__(
        self, vector[CyJob]& jobs, vector[int] C
    ):
        self.jobs = jobs
        self.C = C

    cdef void add_job(Sigma2 self, CyJob& job):
        self.jobs.insert(self.jobs.begin(), job)
        self._update_values(job)

    cpdef Sigma2 copy(Sigma2 self):
        return Sigma2(vector[CyJob](self.jobs), vector[int](self.C))

    cdef void _update_values(Sigma2 self, CyJob& job):
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
