# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp.vector cimport vector

import numpy as np


cdef class Job:

    def __init__(
        self,
        int j,
        const int[::1] p,
        vector[int] r,
        vector[int] q,
        const int[:, ::1] lat,
        int slope,
        int T
    ):
        self.j = j
        self.p = p
        self.r = r
        self.q = q
        self.lat = lat
        self.slope = slope
        self.T = T

    cpdef Job pycopy(Job self):
        return self.copy()

    cdef Job copy(Job self):
        cdef:
            Job job
        job = Job.__new__(Job)
        job.j = self.j
        job.p = self.p
        job.r = vector[int](self.r)
        job.q = vector[int](self.q)
        job.lat = self.lat
        job.slope = self.slope
        job.T = self.T

        return job


cdef Job start_job(int j, const int[::1] p):
    cdef:
        int i, m, m1, m2, T, sum_p, k, slope
        vector[int] r, q
        int[:, ::1] lat
        Job job

    m = <int>len(p)

    r = vector[int](m, 0)
    q = vector[int](m, 0)

    # Resize `lat` to m x m
    lat = np.zeros((m, m), dtype='i')[:, :]

    # Compute sums
    T = 0
    for m1 in range(m):
        T += p[m1]
        for m2 in range(m):
            if m2 + 1 < m1:  # Ensure range is valid
                sum_p = 0
                for i in range(m2 + 1, m1):
                    sum_p += p[i]
                lat[m1, m2] = sum_p

    m += 1
    slope = 0
    for k in range(1, m):
        slope += (k - (m + 1) / 2) * p[k - 1]

    job = Job.__new__(Job)
    job.j = j
    job.p = p
    job.r = r
    job.q = q
    job.lat = lat
    job.slope = slope
    job.T = T

    return job
