# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.memory cimport make_shared, shared_ptr


cdef extern from "job.h":

    cdef cppclass Job:
        const int j
        const vector[int] p
        vector[int] r
        vector[int] q
        vector[vector[int]] lat
        int slope
        int T

        # Declare the constructors
        # Default constructor
        Job()

         # Only id and processing times
        Job(
            const int j_,
            const vector[int] p_
        )

        # Parameterized constructor
        Job(
            const int j_,
            const vector[int] p_,
            vector[int] r_,
            vector[int] q_,
            vector[vector[int]] lat_,
            int slope_,
            int T_
        )


ctypedef shared_ptr[Job] JobPtr
# ctypedef Job* JobPtr


cdef JobPtr start_job(int& j, vector[int]& p) except *


cdef JobPtr copy_job(shared_ptr[Job]& jobptr) except *


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
