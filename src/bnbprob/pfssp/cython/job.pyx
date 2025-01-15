# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libc.stdlib cimport malloc, free
from libcpp.memory cimport make_shared, shared_ptr
from libcpp.vector cimport vector

from cython.operator cimport dereference as deref

INIT_ERROR = 'C++ Job shared pointer not initialized'


cdef JobPtr start_job(int& j, vector[int]& p) except *:
    cdef:
        int i, m, m1, m2, sum_p, k, slope
        vector[int] _l
        shared_ptr[vector[int]] p_
        JobPtr jobptr
        Job* job

    # Create the shared pointer and a regular pointer
    # referencing it's memory location
    p_ = make_shared[vector[int]](p)
    jobptr = make_shared[Job](j, p_)
    job = &deref(jobptr)

    # Number of machines
    m = <int> p.size()

    # Assign attributes
    job.r = vector[int](m, 0)
    job.q = vector[int](m, 0)

    # Compute sums
    job.T = 0
    job.lat = make_shared[vector[vector[int]]](m)
    for m1 in range(m):
        deref(job.lat)[m1] = vector[int](m, 0)
        job.T += p[m1]
        for m2 in range(m):
            if m2 + 1 < m1:  # Ensure range is valid
                sum_p = 0
                for i in range(m2 + 1, m1):
                    sum_p += p[i]
                deref(job.lat)[m1][m2] = sum_p

    # Slope
    m += 1
    job.slope = 0
    for k in range(1, m):
        job.slope += (k - (m + 1) / 2) * p[k - 1]

    return jobptr


cdef JobPtr copy_job(shared_ptr[Job]& jobptr):
    return make_shared[Job](
        deref(jobptr).j,
        deref(jobptr).p,
        deref(jobptr).r,
        deref(jobptr).q,
        deref(jobptr).lat,
        deref(jobptr).slope,
        deref(jobptr).T
    )


cdef class PyJob:

    @property
    def j(self):
        return self.get_j()

    @property
    def p(self):
        return self.get_p()

    @property
    def r(self):
        return self.get_r()

    @property
    def q(self):
        return self.get_q()

    @property
    def lat(self):
        return self.get_lat()

    @property
    def T(self):
        return self.get_T()

    @property
    def slope(self):
        return self.get_slope()

    @staticmethod
    def from_p(int j, list[int] p):
        cdef:
            int N, i
            int* _p
            PyJob out

        out = PyJob.__new__(PyJob)
        out.job = start_job(j, p)
        return out

    cpdef int get_j(self) except *:
        if self.job == NULL:
            raise ReferenceError(INIT_ERROR)
        return deref(self.job).j

    cpdef list[int] get_p(self) except *:
        cdef:
            int i, pi
            list[int] out
        if self.job == NULL:
            raise ReferenceError(INIT_ERROR)
        out = []
        for i in range(deref(deref(self.job).p).size()):
            pi = deref(deref(self.job).p)[i]
            out.append(pi)
        return out

    cpdef list[int] get_r(self) except *:
        cdef:
            int i, ri
            list[int] out
        if self.job == NULL:
            raise ReferenceError(INIT_ERROR)
        out = []
        for i in range(deref(self.job).r.size()):
            ri = deref(self.job).r[i]
            out.append(ri)
        return out

    cpdef list[int] get_q(self) except *:
        cdef:
            int i, qi
            list[int] out
        if self.job == NULL:
            raise ReferenceError(INIT_ERROR)
        out = []
        for i in range(deref(self.job).q.size()):
            qi = deref(self.job).q[i]
            out.append(qi)
        return out

    cpdef list[int] get_lat(self) except *:
        cdef:
            int i, j, li
            list[int] lati
            list[list[int]] out
        if self.job == NULL:
            raise ReferenceError(INIT_ERROR)
        out = []
        for i in range(deref(deref(self.job).lat).size()):
            out.append([])
            for j in range(deref(deref(self.job).lat)[i].size()):
                li = deref(deref(self.job).lat)[i][j]
                out[i].append(li)
        return out

    cpdef int get_slope(self) except *:
        if self.job == NULL:
            raise ReferenceError(INIT_ERROR)
        return deref(self.job).slope

    cpdef int get_T(self) except *:
        if self.job == NULL:
            raise ReferenceError(INIT_ERROR)
        return deref(self.job).T


cdef PyJob job_to_py(JobPtr& jobptr) except *:
    cdef:
        PyJob out
    if jobptr == NULL:
        raise ReferenceError(INIT_ERROR)
    out = PyJob.__new__(PyJob)
    out.job = jobptr
    return out
