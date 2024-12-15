# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True

from array import array


cdef class Job:

    cdef public:
        int j
        int[:] p
        int[:] r
        int[:] q
        int[:, :] lat
        int slope
        int T

    cpdef Job copy(Job self) except *


cpdef Job start_job(int j, int[:] p) except *
