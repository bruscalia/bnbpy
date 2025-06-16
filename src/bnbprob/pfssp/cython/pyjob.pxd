# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp.vector cimport vector

from bnbprob.pfssp.cpp.environ cimport JobPtr

cdef class PyJob:

    cdef:
        JobPtr job

    cpdef int get_j(self) except *

    cpdef list[int] get_p(self) except *

    cpdef list[int] get_r(self) except *

    cpdef list[int] get_q(self) except *

    cpdef list[int] get_lat(self) except *

    cpdef int get_slope(self) except *

    cpdef int get_T(self) except *


cdef PyJob job_to_py(JobPtr& jobptr) except *