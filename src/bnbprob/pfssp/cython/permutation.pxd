# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector

from bnbprob.pfssp.cython.job cimport Job, JobPtr, PyJob
from bnbprob.pfssp.cython.sequence cimport (
    PySigma,
    Sigma
)


cdef class Permutation:

    cdef:
        vector[Job] own_jobs
        vector[JobPtr] free_jobs
        Sigma sigma1
        Sigma sigma2

    cdef public:
        int m
        int n
        int level
        bool unsafe_alloc

    cpdef void clean_jobs(Permutation self)

    cdef void _clean_jobs(Permutation self)

    cpdef list[PyJob] get_free_jobs(Permutation self)

    cdef vector[JobPtr] _get_free_jobs(Permutation self)

    cpdef PySigma get_sigma1(Permutation self)

    cdef Sigma _get_sigma1(Permutation self)

    cpdef PySigma get_sigma2(Permutation self)

    cdef Sigma _get_sigma2(Permutation self)

    cdef vector[JobPtr] get_sequence(Permutation self)

    cdef vector[Job] get_sequence_copy(Permutation self)

    cdef bool is_feasible(Permutation self)

    cdef void _push_job(Permutation self, int j)

    cpdef void push_job(Permutation self, int j)

    cpdef void update_params(Permutation self)

    cdef void _update_params(Permutation self)

    cdef void front_updates(Permutation self)

    cdef void back_updates(Permutation self)

    cpdef void compute_starts(Permutation self)

    cdef void _compute_starts(Permutation self)

    cpdef int calc_lb_1m(Permutation self)

    cpdef int calc_lb_2m(Permutation self)

    cpdef int calc_lb_full(Permutation self)

    cdef int _calc_lb_full(Permutation self)

    cdef int lower_bound_1m(Permutation self)

    cdef int lower_bound_2m(Permutation self)

    cdef vector[int] get_r(Permutation self)

    cdef vector[int] get_q(Permutation self)

    cpdef Permutation copy(Permutation self)

    cdef Permutation _copy(Permutation self)


cdef Permutation start_perm(int m, vector[Job]& jobs)


ctypedef struct JobParams:
    int t1
    int t2
    const int* p1
    const int* p2
    const int* lat


cdef int two_mach_problem(vector[JobPtr]& jobs, int m1, int m2)


cdef int two_mach_makespan(
    vector[JobParams]& job_times,
    int m1,
    int m2
)
