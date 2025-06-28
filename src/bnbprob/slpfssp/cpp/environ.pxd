# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.memory cimport shared_ptr


cdef extern from "job.hpp":

    cdef cppclass Job:
        int j
        shared_ptr[vector[vector[int]]] p
        vector[vector[int]] r
        vector[vector[int]] q
        shared_ptr[vector[vector[vector[int]]]] lat
        shared_ptr[vector[int]] m
        int L
        int s

        # Declare the constructors
        # Default constructor
        inline Job()

        # Constructor with job ID and shared_ptr for processing times
        inline Job(
            const int &j_,
            const shared_ptr[vector[vector[int]]] &p_
        )

        # Constructor with job ID and vector for processing times (creates shared_ptr internally)
        inline Job(const int &j_, const vector[vector[int]] &p_)

        # Parameterized constructor
        inline Job(
            const int &j_,
            const shared_ptr[vector[vector[int]]] &p_,
            const vector[vector[int]] &r_,
            const vector[vector[int]] &q_,
            const shared_ptr[vector[vector[vector[int]]]] &lat_,
            const shared_ptr[vector[int]] &m_,
            const int &s_ = 1
        )

        # Get T
        int get_T() const

    # Function to copy a job
    cdef inline shared_ptr[Job] copy_job(const shared_ptr[Job]& jobptr)

    # Function to copy a vector of jobs
    cdef vector[shared_ptr[Job]] copy_jobs(const vector[shared_ptr[Job]]& jobs)


ctypedef shared_ptr[Job] JobPtr


cdef extern from "sigma.hpp":

    cdef cppclass Sigma:
        shared_ptr[vector[int]] m
        vector[shared_ptr[Job]] jobs
        vector[vector[int]] C

        # Default constructor
        inline Sigma()

        # Constructor with empty instance
        inline Sigma(const shared_ptr[vector[int]] &m_)

        # Constructor with only jobs
        inline Sigma(const shared_ptr[vector[int]] &m_, const vector[shared_ptr[Job]] &jobs_)

        # Full constructor
        inline Sigma(const shared_ptr[vector[int]] &m_, const vector[shared_ptr[Job]] &jobs_, const vector[vector[int]] &C_)
