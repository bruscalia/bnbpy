# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp.vector cimport vector

from bnbprob.pafssp.cpp.environ cimport Job, JobPtr

cdef class PyJob:

    cdef:
        Job job

    cdef Job get_job(self)

    cpdef int get_j(self) except *

    cpdef list[int] get_p(self) except *

    cpdef list[int] get_r(self) except *

    cpdef list[int] get_q(self) except *

    cpdef list[list[int]] get_lat(self) except *

    cpdef list[int] get_s(self) except *

    cpdef int get_slope(self) except *

    cpdef int get_T(self) except *


cdef PyJob job_to_py(JobPtr& jobptr) except *