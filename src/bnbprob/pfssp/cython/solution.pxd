# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True

from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.algorithm cimport sort

from bnbprob.pfssp.cython.job cimport CyJob, copy_job, start_job
from bnbprob.pfssp.cython.sequence cimport Sigma

from enum import Enum

from bnbpy.status import OptStatus


cdef:
    int LARGE_INT = 10000000


cdef class CyPermutation:

    cdef public:
        int m, level, cost, lb
        vector[CyJob] free_jobs
        Sigma sigma1
        Sigma sigma2
        object status

    cpdef void assign(
        CyPermutation self,
        int m,
        vector[CyJob]& free_jobs,
        Sigma& sigma1,
        Sigma& sigma2,
        int level
    )

    cdef vector[CyJob] get_sequence(CyPermutation self)

    cdef vector[CyJob] get_sequence_copy(CyPermutation self)

    cpdef int calc_bound(CyPermutation self)

    cpdef bool is_feasible(CyPermutation self)

    cpdef void push_job(CyPermutation self, int& j)

    cpdef void update_params(CyPermutation self)

    cdef void front_updates(CyPermutation self)

    cdef void back_updates(CyPermutation self)

    cpdef int calc_lb_1m(CyPermutation self)

    cpdef int calc_lb_2m(CyPermutation self)

    cpdef int calc_lb_full(CyPermutation self)

    cpdef void compute_starts(CyPermutation self)

    cpdef int lower_bound_1m(CyPermutation self)

    cpdef int lower_bound_2m(CyPermutation self)

    cdef vector[int] get_r(self)

    cdef vector[int] get_q(self)

    cpdef CyPermutation quick_constructive(CyPermutation self)

    cpdef CyPermutation neh_constructive(CyPermutation self)

    cpdef CyPermutation local_search(CyPermutation self)

    cpdef CyPermutation copy(CyPermutation self)


cdef struct TwoMachParam:
    CyJob *job
    int t1
    int t2


ctypedef TwoMachParam* TwoMachParamPtr


cdef inline int desc_slope(const CyJob& a, const CyJob& b):
    return b.slope < a.slope  # Desc order based on slope


cdef inline int desc_T(const CyJob& a, const CyJob& b):
    return b.T < a.T  # Desc order based on slope


cdef inline int asc_t1(const TwoMachParam& a, const TwoMachParam& b):
    return a.t1 < b.t1  # Ascending order based on t1


cdef inline int desc_t2(const TwoMachParam& a, const TwoMachParam& b):
    return b.t2 < a.t2  # Descending order based on t2


cdef void recompute_r0(vector[CyJob]& jobs)


cdef int two_mach_problem(vector[CyJob]& jobs, int& m1, int& m2)


cdef int two_mach_makespan(
    vector[TwoMachParam]& job_times,
    int& m1,
    int& m2
)
