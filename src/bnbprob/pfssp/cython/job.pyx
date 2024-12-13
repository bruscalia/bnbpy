# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True


cdef class Job:

    def __init__(
        self,
        int j,
        list[int] p not None,
        list[int] r not None,
        list[int] q not None,
        list[list[int]] lat not None,
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

    cpdef Job copy(Job self) except *:
        return Job(
            self.j,
            self.p,
            self.r.copy(),
            self.q.copy(),
            self.lat,
            self.slope,
            self.T
        )


cpdef Job start_job(int j, list[int] p) except *:
    cdef:
        int i, m, m1, m2, T, sum_p, k, slope
        list[int] r, q
        list[list[int]] lat

    m = <int>len(p)

    r = [0] * m
    q = [0] * m

    # Resize `lat` to m x m
    lat = [[0 for _ in range(m)] for _ in range(m)]

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

    m += 1
    slope = 0
    for k in range(1, m):
        slope += (k - (m + 1) / 2) * p[k - 1]

    return Job(j, p, r, q, lat, slope, T)
