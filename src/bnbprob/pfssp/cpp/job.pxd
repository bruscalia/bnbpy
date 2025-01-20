# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.memory cimport shared_ptr


cdef extern from "job.hpp":

    cdef cppclass Job:
        int j
        shared_ptr[vector[int]] p
        vector[int] r
        vector[int] q
        shared_ptr[vector[vector[int]]] lat
        int slope
        int T

        # Declare the constructors
        # Default constructor
        inline Job()

        # Constructor with job ID and shared_ptr for processing times
        inline Job(
            const int &j_,
            const shared_ptr[vector[int]] &p_
        )

        # Constructor with job ID and vector for processing times (creates shared_ptr internally)
        inline Job(const int &j_, const vector[int] &p_)

        # Parameterized constructor
        inline Job(
            const int &j_,
            const shared_ptr[vector[int]] &p_,
            const vector[int] &r_,
            const vector[int] &q_,
            const shared_ptr[vector[vector[int]]] &lat_,
            const int &slope_,
            const int &T_
        )

    # Function to copy a job
    cdef inline shared_ptr[Job] copy_job(const shared_ptr[Job]& jobptr)

    # Function to copy a vector of jobs
    cdef vector[shared_ptr[Job]] copy_jobs(const vector[shared_ptr[Job]]& jobs)


ctypedef shared_ptr[Job] JobPtr

ctypedef shared_ptr[Job] JobPtrAlter
