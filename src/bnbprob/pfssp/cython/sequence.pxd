# distutils: language = c++
# cython: language_level=3, boundscheck=True, wraparound=True, cdivision=True

from libcpp.vector cimport vector

from bnbprob.pfssp.cython.job cimport Job


cdef class Sigma1:
    cdef public:
        list[Job] jobs
        vector[int] C

    cdef void add_job(Sigma1 self, Job job)
    cdef Sigma1 copy(Sigma1 self)
    cdef void _update_values(Sigma1 self, Job job)


cdef class Sigma2:
    cdef public:
        list[Job] jobs
        vector[int] C

    cdef void add_job(Sigma2 self, Job job)
    cdef Sigma2 copy(Sigma2 self)
    cdef void _update_values(Sigma2 self, Job job)
