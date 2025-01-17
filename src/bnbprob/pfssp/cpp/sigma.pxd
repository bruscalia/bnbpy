# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.memory cimport shared_ptr

from bnbprob.pfssp.cpp.job cimport JobPtr


cdef extern from "sigma.hpp":

    cdef cppclass Sigma:
        int m
        vector[JobPtr] jobs
        vector[int] C

        # Default constructor
        Sigma()

        # Constructor with empty instance
        Sigma(int& m_)

        # Constructor with only jobs
        Sigma(int& m_, vector[JobPtr]& jobs_)

        # Full constructor
        Sigma(int& m_, vector[JobPtr]& jobs_, vector[int]& C_)

        # Push job to the bottom of the sequence
        void job_to_bottom(JobPtr& job)

        # Push job to the top of the sequence
        void job_to_top(JobPtr& job)


ctypedef shared_ptr[Sigma] SigmaPtret
