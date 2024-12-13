# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True

from libcpp.vector cimport vector


cdef struct CyJob:
    int j
    vector[int] p
    vector[int] r
    vector[int] q
    vector[vector[int]] lat
    int slope
    int T


ctypedef CyJob* CyJobPtr


cdef class PyJob:
    cdef:
        CyJob job


cdef CyJob start_job(int& j, vector[int]& p)


cdef CyJob copy_job(CyJob& job)
