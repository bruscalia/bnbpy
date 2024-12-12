# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True

from libcpp.vector cimport vector

from typing import List


cdef class Job:

    def __init__(
        self,
        int j,
        vector[int] p,
        vector[int] r,
        vector[int] q,
        vector[vector[int]] lat
    ):
        self._j = j
        self.p = p
        self.r = r
        self.q = q
        self.lat = lat
        # Overwrite later, but not on init to avoid unnecessary calculations
        self.slope = 0
        self.T = 0

    @property
    def _signature(self):
        return f'Job {self.j}'

    @property
    def j(self) -> int:
        return self._j

    cdef void cfill_start(Job self, int m):
        cdef:
            int m1, m2, k, i, sum_p

        self.r = vector[int](m, 0)
        self.q = vector[int](m, 0)

        # Resize `lat` to m x m
        self.lat.resize(m)
        for m1 in range(m):
            self.lat[m1].resize(m)

        # Compute sums
        self.T = 0
        for m1 in range(m):
            self.T += self.p[m1]
            for m2 in range(m):
                if m2 + 1 < m1:  # Ensure range is valid
                    sum_p = 0
                    for i in range(m2 + 1, m1):
                        sum_p += self.p[i]
                    self.lat[m1][m2] = sum_p
                else:
                    self.lat[m1][m2] = 0  # Default to 0 if range is invalid
        m += 1
        self.slope = 0
        for k in range(1, m):
            self.slope += (k - (m + 1) / 2) * self.p[k - 1]

    cdef void set_to_r(Job self, int m, int val):
        self.r[m] = val

    cdef void set_to_q(Job self, int m, int val):
        self.q[m] = val

    cdef Job ccopy(Job self):
        cdef:
            Job other

        other = Job(
            self.j,
            self.p,
            vector[int](self.r),
            vector[int](self.q),
            self.lat,
        )
        other.slope = self.slope
        return other

    def pyset_to_r(self, m: int, val: int):
        self.set_to_r(m, val)

    def pyset_to_q(self, m: int, val: int):
        self.set_to_r(m, val)

    def fill_start(self, m: int):
        return self.cfill_start(m)

    def copy(self) -> Job:
        return self.ccopy()

    def get_p(self) -> List[int]:
        return [i for i in self.p]

    def get_r(self) -> List[int]:
        return [i for i in self.r]

    def get_q(self) -> List[int]:
        return [i for i in self.q]

    def get_lat(self) -> List[List[int]]:
        return [[i for i in l] for l in self.lat]
