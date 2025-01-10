# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector


ctypedef struct Job:
    int j
    int* p
    vector[int] r
    vector[int] q
    int** lat
    int slope
    int T


ctypedef Job* JobPtr


cdef void fill_job(Job* job, j, list[int] p) except *

cdef Job start_job(int j, list[int] p)

cdef void free_job(Job& job)


cdef class PyJob:

    cdef:
        Job job
        bool unsafe_alloc

    cpdef int get_T(self)

    cpdef int get_j(self)

    cpdef int get_p(self, int i)

    cpdef int get_r(self, int i)

    cpdef int get_lat(self, int i, int j)
