# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.memory cimport shared_ptr


cdef extern from "job.hpp":

    cdef cppclass Job:
        int j
        shared_ptr[vector[int]] p
        vector[int] r
        vector[int] q
        shared_ptr[vector[vector[int]]] lat
        int slope
        int T

        # Declare the constructors
        # Default constructor
        inline Job()

        # Constructor with job ID and shared_ptr for processing times
        inline Job(
            const int &j_,
            const shared_ptr[vector[int]] &p_
        )

        # Constructor with job ID and vector for processing times (creates shared_ptr internally)
        inline Job(const int &j_, const vector[int] &p_)

        # Parameterized constructor
        inline Job(
            const int &j_,
            const shared_ptr[vector[int]] &p_,
            const vector[int] &r_,
            const vector[int] &q_,
            const shared_ptr[vector[vector[int]]] &lat_,
            const int &slope_,
            const int &T_
        )

    # Function to copy a job
    cdef inline shared_ptr[Job] copy_job(const shared_ptr[Job]& jobptr)

    # Function to copy a vector of jobs
    cdef vector[shared_ptr[Job]] copy_jobs(const vector[shared_ptr[Job]]& jobs)


ctypedef shared_ptr[Job] JobPtr


cdef extern from "sigma.hpp":

    cdef cppclass Sigma:
        int m
        vector[shared_ptr[Job]] jobs
        vector[int] C

        # Default constructor
        inline Sigma()

        # Constructor with empty instance
        inline Sigma(const int &m_)

        # Constructor with only jobs
        inline Sigma(const int &m_, const vector[shared_ptr[Job]] &jobs_)

        # Full constructor
        inline Sigma(const int &m_, const vector[shared_ptr[Job]] &jobs_, const vector[int] &C_)

        # Push job to the bottom of the sequence
        void job_to_bottom(const shared_ptr[Job] &job)

        # Push job to the top of the sequence
        void job_to_top(const shared_ptr[Job] &job)


cdef extern from "permutation.hpp":

    cdef cppclass Permutation:
        int m
        int n
        int level
        Sigma sigma1
        vector[shared_ptr[Job]] free_jobs
        Sigma sigma2

        # Default constructor
        inline Permutation()

        # Constructor from processing times
        Permutation(const vector[vector[int]]& p_)

        # Constructor from free jobs
        inline Permutation(const int &m_, const vector[shared_ptr[Job]] &jobs_)

        # Constructor given all desired attributes
        inline Permutation(
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
        inline bool is_feasible()

        # Lower bound calculations
        inline int calc_lb_1m()
        inline int calc_lb_2m()
        int calc_lb_full()
        int lower_bound_1m()
        int lower_bound_2m()

        # Copy method
        inline Permutation copy() const

    cdef cppclass JobParams:
        int t1
        int t2
        const int* p1
        const int* p2
        const int* lat

        # Constructors
        inline JobParams(const int &t1_, const int &t2_, const int* &p1_, const int* &p2_, const int* &lat_)
        inline JobParams(const int &t1_, const int &t2_, const int &p1_, const int &p2_, const int &lat_)

    # Two machine problem definition
    int two_mach_problem(const vector[shared_ptr[Job]] &jobs, const int &m1, const int &m2)

    # Makespan given ordered operations
    int two_mach_makespan(
        const vector[JobParams] &job_times,
        const int &m1,
        const int &m2
    )


cdef extern from "local_search.hpp":

    cdef Permutation local_search(Permutation &perm)


cdef extern from "neh.hpp":

    cdef Permutation neh_constructive(vector[shared_ptr[Job]] &jobs)


cdef extern from "quick_constructive.hpp":

    cdef Permutation quick_constructive(vector[shared_ptr[Job]] &jobs)
