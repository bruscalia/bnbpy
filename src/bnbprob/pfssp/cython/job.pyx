# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from array import array

import numpy as np


cdef class Job:

    def __init__(
        self,
        int j,
        const int[::1] p,
        int[::1] r,
        int[::1] q,
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

    cpdef Job copy(Job self):
        return Job(
            self.j,
            self.p,
            self.r.copy(),
            self.q.copy(),
            self.lat,
            self.slope,
            self.T
        )


cdef Job start_job(int j, const int[::1] p):
    cdef:
        int i, m, m1, m2, T, sum_p, k, slope
        int[::1] r, q
        int[:, ::1] lat

    m = <int>len(p)

    r = array('i', [0] * m)[:]
    q = array('i', [0] * m)[:]

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

    return Job(
        j,
        p,
        r,
        q,
        lat,
        slope,
        T
    )
