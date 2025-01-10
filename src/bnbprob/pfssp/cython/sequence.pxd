from libcpp.vector cimport vector

from bnbprob.pfssp.cython.job cimport JobPtr, PyJob

cdef struct Sigma:
    vector[JobPtr] jobs
    vector[int] C
    int m


cdef void job_to_bottom(Sigma& sigma, JobPtr& job)


cdef void job_to_top(Sigma& sigma, JobPtr& job)


cdef Sigma empty_sigma(int& m)


cdef class PySigma:
    cdef:
        Sigma sigma

    cpdef list[PyJob] get_jobs(PySigma self)

    cpdef vector[int] get_C(PySigma self)

    cpdef void job_to_bottom(PySigma self, PyJob job)

    cpdef void job_to_top(PySigma self, PyJob job)
