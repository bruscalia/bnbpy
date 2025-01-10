# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libc.stdlib cimport malloc, free
from libcpp.vector cimport vector


cdef Job start_job(int j, list[int] p):
    cdef:
        int i, m, m1, m2, T, sum_p, k, slope
        int* _p, _l
        int** lat
        vector[int] r, q
        Job job

    m = <int>len(p)

    r = vector[int](m, 0)
    q = vector[int](m, 0)

    # Pointers
    _p = <int *> malloc(m * sizeof(int))
    lat = <int**>malloc(m * sizeof(int*))

    # Compute sums
    T = 0
    for m1 in range(m):
        lat[m1] = <int*>malloc(m * sizeof(int))
        _p[m1] = p[m1]
        T += p[m1]
        for m2 in range(m):
            if m2 + 1 < m1:  # Ensure range is valid
                sum_p = 0
                for i in range(m2 + 1, m1):
                    sum_p += p[i]
                lat[m1][m2] = sum_p
            else:
                lat[m1][m2] = 0

    m += 1
    slope = 0
    for k in range(1, m):
        slope += (k - (m + 1) / 2) * p[k - 1]

    job = Job(
        j,
        _p,
        r,
        q,
        lat,
        slope,
        T
    )

    return job


cdef Job free_job(Job& job):
    cdef:
        int i
    free(job.p)
    for i in range(job.r.size()):
        free(job.lat[i])
    free(job.lat)


cdef class JobClass:

    cdef:
        Job job

    def __delloc__(self):
        free_job(self.job)

    @staticmethod
    def from_p(int j, list[int] p):
        cdef:
            int N, i
            int* _p
            Job job
            JobClass out

        job = start_cjob(j, p)
        out = JobClass.__new__(JobClass)
        out.job = job
        return out

    cpdef int get_p(self, int i):
        return self.job.p[i]

    cpdef int get_r(self, int i):
        return self.job.r[i]

    cpdef int get_lat(self, int i, int j):
        return self.job.lat[i][j]
