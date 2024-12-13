# distutils: language = c++
# cython: language_level=3, boundscheck=True, wraparound=True, cdivision=True

from libcpp.vector cimport vector

from bnbprob.pfssp.cython.job cimport CyJob


cdef struct Sigma:
    vector[CyJob] jobs
    vector[int] C


cdef void job_to_bottom(Sigma& sigma, CyJob& job)


cdef void job_to_top(Sigma& sigma, CyJob& job)


cpdef Sigma copy_sigma(Sigma& sigma)


cdef class Sigma1:
    cdef public:
        vector[CyJob] jobs
        vector[int] C

    cdef void add_job(Sigma1 self, CyJob job)

    cpdef Sigma1 copy(Sigma1 self)

    cdef void _update_values(Sigma1 self, CyJob job)


cdef class Sigma2:
    cdef public:
        vector[CyJob] jobs
        vector[int] C

    cdef void add_job(Sigma2 self, CyJob job)

    cpdef Sigma2 copy(Sigma2 self)

    cdef void _update_values(Sigma2 self, CyJob job)
