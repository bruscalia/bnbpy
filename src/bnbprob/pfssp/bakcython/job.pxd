# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp.vector cimport vector


cdef struct Job:
    int j
    int* p
    vector[int] r
    vector[int] q
    int** lat
    int slope
    int T


cdef Job start_job(int j, list[int] p)

cdef Job free_job(Job& job)
