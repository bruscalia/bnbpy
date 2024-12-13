# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True


cdef class Job:

    cdef public:
        int j
        list[int] p
        list[int] r
        list[int] q
        list[list[int]] lat
        int slope
        int T

    cpdef Job copy(Job self) except *


cpdef Job start_job(int j, list[int] p) except *
