# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True

from libcpp.vector cimport vector


cdef class Job:

    cdef:
        int _j

    cdef public:
        int slope
        int T
        vector[int] p
        vector[int] r
        vector[int] q
        vector[vector[int]] lat

    cdef void cfill_start(Job self, int m)
    cdef void set_to_r(Job self, int m, int val)
    cdef void set_to_q(Job self, int m, int val)
    cdef Job ccopy(Job self)
