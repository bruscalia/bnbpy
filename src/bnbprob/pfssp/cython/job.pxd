# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.memory cimport make_shared, shared_ptr

from cython.operator cimport dereference as deref


cdef extern from "job.h":

    cdef cppclass Job:
        int j
        shared_ptr[vector[int]] p
        vector[int] r
        vector[int] q
        shared_ptr[vector[vector[int]]] lat
        int slope
        int T

        # Declare the constructors
        # Constructor with job ID and shared_ptr for processing times
        Job(
            int j_,
            shared_ptr[vector[int]]& p_
        )

        # Constructor with job ID and vector for processing times (creates shared_ptr internally)
        Job(int j_, vector[int]& p_)

        # Parameterized constructor
        Job(
            int j_,
            shared_ptr[vector[int]]& p_,
            vector[int] r_,
            vector[int] q_,
            shared_ptr[vector[vector[int]]]& lat_,
            int slope_,
            int T_
        )

    # Function to start a job with a given job ID and processing times
    cdef inline shared_ptr[Job] start_job(int& j, vector[int]& p)

    # Function to copy a job
    cdef inline shared_ptr[Job] copy_job(shared_ptr[Job]& jobptr)

    # Function to copy a vector of jobs
    cdef vector[shared_ptr[Job]] copy_jobs(vector[shared_ptr[Job]]& jobs) nogil


ctypedef shared_ptr[Job] JobPtr

ctypedef Job* Joboip


# Function to start a job with a given job ID and processing times
# cdef inline JobPtr start_job(int& j, vector[int]& p):
#     return make_shared[Job](j, p)

# Function to copy a job
# cdef inline JobPtr copy_job(shared_ptr[Job]& jobptr):
#     return make_shared[Job](
#         deref(jobptr).j,
#         deref(jobptr).p,
#         deref(jobptr).r,
#         deref(jobptr).q,
#         deref(jobptr).lat,
#         deref(jobptr).slope,
#         deref(jobptr).T
#     )
