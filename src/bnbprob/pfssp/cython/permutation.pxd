# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector

from bnbprob.pfssp.cython.job cimport Job
from bnbprob.pfssp.cython.sequence cimport Sigma


cdef class Permutation:

    cdef public:
        int m
        list[Job] free_jobs
        Sigma sigma1
        Sigma sigma2
        int level

    cpdef void cleanup(Permutation self)

    cpdef list[Job] get_sequence(Permutation self)

    cpdef list[Job] get_sequence_copy(Permutation self)

    cpdef int calc_bound(Permutation self)

    cpdef bool is_feasible(Permutation self)

    cpdef void push_job(Permutation self, int j)

    cpdef void update_params(Permutation self)

    cdef void front_updates(Permutation self)

    cdef void back_updates(Permutation self)

    cpdef int calc_lb_1m(Permutation self)

    cpdef int calc_lb_2m(Permutation self)

    cpdef int calc_lb_full(Permutation self)

    cpdef void compute_starts(Permutation self)

    cpdef int lower_bound_1m(Permutation self)

    cpdef int lower_bound_2m(Permutation self)

    cdef vector[int] get_r(Permutation self)

    cdef vector[int] get_q(Permutation self)

    cpdef Permutation copy(Permutation self)


cpdef Permutation start_perm(int m, list[Job] free_jobs)


ctypedef struct JobParams:
    int t1
    int t2
    const int* p1
    const int* p2
    const int* lat


cdef int two_mach_problem(list[Job] jobs, int m1, int m2)


cdef int two_mach_makespan(
    vector[JobParams] &job_times,
    int m1,
    int m2
)
