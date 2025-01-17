# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.memory cimport shared_ptr

from bnbprob.pfssp.cpp.job cimport JobPtr
from bnbprob.pfssp.cpp.sigma cimport Sigma


cdef extern from "permutation.hpp":

    cdef cppclass Permutation:
        int m
        int n
        int level
        Sigma sigma1
        vector[JobPtr] free_jobs
        Sigma sigma2

        # Default constructor
        Permutation()

        # Constructor from processing times
        Permutation(vector[vector[int]]& p_)

        # Constructor from free jobs
        Permutation(int m_, vector[JobPtr] jobs_)

        # Constructor given all desired attributes
        Permutation(
            int m_, int n_, int level_,
            Sigma sigma1_, vector[JobPtr] free_jobs_, Sigma sigma2_
        )

        # Accessor methods
        vector[JobPtr]& get_free_jobs()
        Sigma* get_sigma1()
        Sigma* get_sigma2()
        vector[JobPtr] get_sequence()
        vector[JobPtr] get_sequence_copy()
        vector[int] get_r()
        vector[int] get_q()

        # Modification methods
        void push_job(int& j)
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
        int* p1
        int* p2
        int* lat

        # Constructors
        JobParams(int t1_, int t2_, int* p1_, int* p2_, int* lat_)
        JobParams(int t1_, int t2_, int& p1_, int& p2_, int& lat_)

    # Two machine problem definition
    int two_mach_problem(vector[JobPtr]& jobs, int& m1, int& m2)

    # Makespan given ordered operations
    int two_mach_makespan(
        vector[JobParams]& job_times,
        int& m1,
        int& m2
    )


ctypedef Permutation* PermPtr