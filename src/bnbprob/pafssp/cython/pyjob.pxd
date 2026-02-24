# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp.vector cimport vector

from bnbprob.pafssp.cpp.environ cimport Job, JobPtr

cdef class PyJob:

    cdef:
        Job job

    cdef JobPtr get_job(self)

    cpdef int get_j(self)

    cpdef list[int] get_p(self)

    cpdef list[int] get_r(self)

    cpdef list[int] get_q(self)

    cpdef list[list[int]] get_lat(self)

    cpdef list[int] get_s(self)

    cpdef int get_slope(self)

    cpdef int get_T(self)


cdef PyJob job_to_py(JobPtr& jobptr)