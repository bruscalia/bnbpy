# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True

from bnbprob.pfssp.cython.job cimport Job


cdef class Sigma:

    cdef public:
        list[Job] jobs
        int[:] C
        int m

    cdef void job_to_bottom(Sigma self, Job job)

    cdef void job_to_top(Sigma self, Job job)

    cdef Sigma copy(Sigma self)
