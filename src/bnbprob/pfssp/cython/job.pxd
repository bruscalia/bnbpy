# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp.vector cimport vector


cdef class Job:

    cdef public:
        int j
        const int[::1] p
        vector[int] r
        vector[int] q
        const int[:, ::1] lat
        int slope
        int T

    cpdef Job pycopy(Job self)

    cdef Job copy(Job self)


cdef Job start_job(int j, const int[::1] p)
