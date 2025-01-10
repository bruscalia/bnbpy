# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libc.stdlib cimport malloc, free
from libcpp.memory cimport make_shared, shared_ptr
from libcpp.vector cimport vector

from cython.operator cimport dereference as deref


cdef void fill_job(JobPtr& job, int& j, vector[int]& p) except *:
    cdef:
        int i, m, m1, m2, T, sum_p, k, slope
        int* _p, _l
        int** lat
        vector[int] r, q

    m = <int> p.size()

    r = vector[int](m, 0)
    q = vector[int](m, 0)

    # Pointers
    _p = <int *> malloc(m * sizeof(int))
    lat = <int**> malloc(m * sizeof(int*))

    # Compute sums
    T = 0
    for m1 in range(m):
        lat[m1] = <int*> malloc(m * sizeof(int))
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

    deref(job).j = j
    deref(job).p = _p
    deref(job).r = r
    deref(job).q = q
    deref(job).lat = lat
    deref(job).slope = slope
    deref(job).T = T


cdef JobPtr start_job(int& j, vector[int]& p):
    cdef:
        JobPtr job

    job = make_shared[Job]()
    # job = new Job()
    fill_job(job, j, p)

    return job


cdef JobPtr copy_job(shared_ptr[Job]& jobptr):
    cdef:
        JobPtr otherptr
        Job* job
        Job* other

    otherptr = make_shared[Job]()
    other = &deref(otherptr)
    job = &deref(jobptr)
    # other = new Job()
    other.j = job.j
    other.p = job.p
    other.r = job.r
    other.q = job.q
    other.lat = job.lat
    other.slope = job.slope
    other.T = job.T

    return otherptr


cdef void free_job(JobPtr& job):
    cdef:
        int i
        Job* job_

    job_ = &deref(job)
    free(job_.p)
    if (job_.lat != NULL):
        for i in range(job_.r.size()):
            free(job_.lat[i])
        free(job_.lat)


cdef class PyJob:

    # def __del__(PyJob self):
    #     if self.unsafe_alloc:
    #         free_job(self.job)
            # del self.job

    @staticmethod
    def from_p(int j, list[int] p):
        cdef:
            int N, i
            int* _p
            PyJob out

        out = PyJob.__new__(PyJob)
        out.unsafe_alloc = True
        out.job = start_job(j, p)
        return out

    cpdef int get_T(self):
        return deref(self.job).T

    cpdef int get_j(self):
        return deref(self.job).j

    cpdef int get_p(self, int i):
        return deref(self.job).p[i]

    cpdef int get_r(self, int i):
        return deref(self.job).r[i]

    cpdef int get_lat(self, int i, int j):
        return deref(self.job).lat[i][j]
