# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp.vector cimport vector

from bnbprob.pfssp.cython.job cimport Job


cdef class Sigma:

    cdef public:
        list[Job] jobs
        vector[int] C
        int m

    cdef void cleanup(Sigma self)

    cdef void job_to_bottom(Sigma self, Job job)

    cdef void job_to_top(Sigma self, Job job)

    cdef Sigma copy(Sigma self)


cdef Sigma empty_sigma(int m)
