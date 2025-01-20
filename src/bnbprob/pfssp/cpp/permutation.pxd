# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.memory cimport shared_ptr

from bnbprob.pfssp.cpp.job cimport Job
from bnbprob.pfssp.cpp.sigma cimport Sigma


cdef extern from "permutation.hpp":

    cdef cppclass Permutation:
        int m
        int n
        int level
        Sigma sigma1
        vector[shared_ptr[Job]] free_jobs
        Sigma sigma2

        # Default constructor
        Permutation()

        # Constructor from processing times
        Permutation(const vector[vector[int]]& p_)

        # Constructor from free jobs
        Permutation(const int &m_, const vector[shared_ptr[Job]] &jobs_)

        # Constructor given all desired attributes
        Permutation(
            const int &m_, const int &n_, const int &level_,
            const Sigma &sigma1_, const vector[shared_ptr[Job]] &free_jobs_,
            const Sigma &sigma2_
        )

        # Accessor methods
        vector[shared_ptr[Job]] *get_free_jobs()
        Sigma *get_sigma1()
        Sigma *get_sigma2()
        vector[shared_ptr[Job]] get_sequence()
        vector[shared_ptr[Job]] get_sequence_copy()
        vector[int] get_r()
        vector[int] get_q()

        # Modification methods
        void push_job(const int &j)
        void update_params()
        void front_updates()
        void back_updates()
        void compute_starts()

        # Feasibility check
        bool is_feasible()

        # Lower bound calculations
        int calc_lb_1m()
        int calc_lb_2m()
        int calc_lb_full()
        int lower_bound_1m()
        int lower_bound_2m()

        # Copy method
        Permutation copy() const

    cdef cppclass JobParams:
        int t1
        int t2
        const int* p1
        const int* p2
        const int* lat

        # Constructors
        JobParams(const int &t1_, const int &t2_, const int* &p1_, const int* &p2_, const int* &lat_)
        JobParams(const int &t1_, const int &t2_, const int &p1_, const int &p2_, const int &lat_)

    # Two machine problem definition
    int two_mach_problem(const vector[shared_ptr[Job]] &jobs, const int &m1, const int &m2)

    # Makespan given ordered operations
    int two_mach_makespan(
        const vector[JobParams] &job_times,
        const int &m1,
        const int &m2
    )


ctypedef Permutation* PermPtr
