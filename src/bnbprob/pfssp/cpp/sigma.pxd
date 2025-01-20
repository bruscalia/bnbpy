# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.memory cimport shared_ptr

from bnbprob.pfssp.cpp.job cimport Job


cdef extern from "sigma.hpp":

    cdef cppclass Sigma:
        int m
        vector[shared_ptr[Job]] jobs
        vector[int] C

        # Default constructor
        Sigma()

        # Constructor with empty instance
        Sigma(const int &m_)

        # Constructor with only jobs
        Sigma(const int &m_, const vector[shared_ptr[Job]] &jobs_)

        # Full constructor
        Sigma(const int &m_, const vector[shared_ptr[Job]] &jobs_, const vector[int] &C_)

        # Push job to the bottom of the sequence
        void job_to_bottom(const shared_ptr[Job] &job)

        # Push job to the top of the sequence
        void job_to_top(const shared_ptr[Job] &job)


ctypedef shared_ptr[Sigma] SigmaPtr
