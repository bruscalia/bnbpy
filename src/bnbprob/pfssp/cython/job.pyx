# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True

from libcpp.vector cimport vector

from typing import List


cdef class PyJob:

    def __init__(
        self,
        CyJob job,
    ):
        self.job = job

    @property
    def j(self) -> int:
        return self.job.j

    @property
    def p(self) -> List[int]:
        return list(self.job.p)

    @property
    def r(self) -> List[int]:
        return list(self.job.r)

    @property
    def q(self) -> List[int]:
        return list(self.job.q)

    @property
    def lat(self) -> List[List[int]]:
        return [[i for i in l] for l in self.job.lat]


cdef CyJob start_job(int& j, vector[int]& p):
    cdef:
        int m, m1, m2, T, sum_p, k, slope
        vector[int] r, q
        vector[vector[int]] lat

    m = <int>p.size()

    r = vector[int](m, 0)
    q = vector[int](m, 0)

    # Resize `lat` to m x m
    lat = vector[vector[int]]()
    lat.resize(m)
    for m1 in range(m):
        lat[m1].resize(m)

    # Compute sums
    T = 0
    for m1 in range(m):
        T += p[m1]
        for m2 in range(m):
            if m2 + 1 < m1:  # Ensure range is valid
                sum_p = 0
                for i in range(m2 + 1, m1):
                    sum_p += p[i]
                lat[m1][m2] = sum_p
            else:
                lat[m1][m2] = 0  # Default to 0 if range is invalid

    m += 1
    slope = 0
    for k in range(1, m):
        slope += (k - (m + 1) / 2) * p[k - 1]

    return CyJob(j, p, r, q, lat, slope, T)


cdef CyJob copy_job(CyJob& job):
    return CyJob(
        job.j,
        job.p,
        vector[int](job.r),
        vector[int](job.q),
        job.lat,
        job.slope,
        job.T
    )
