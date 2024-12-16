# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False


cdef class Job:

    cdef public:
        int j
        const int[::1] p
        int[::1] r
        int[::1] q
        const int[:, ::1] lat
        int slope
        int T

    cpdef Job copy(Job self)


cdef Job start_job(int j, const int[::1] p)
