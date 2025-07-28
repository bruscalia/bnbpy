# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.memory cimport shared_ptr


cdef extern from "job.hpp":

    cdef cppclass Job:
        int j
        shared_ptr[vector[vector[int]]] p
        vector[vector[int]] r
        vector[vector[int]] q
        shared_ptr[vector[vector[vector[int]]]] lat
        shared_ptr[vector[int]] m
        int L
        int s

        # Declare the constructors
        # Default constructor
        Job()

        # Constructor with job ID and shared_ptr for processing times
        Job(
            const int &j_,
            const shared_ptr[vector[vector[int]]] &p_,
            const int &s_ = 1
        )

        Job(
            const int &j_,
            const shared_ptr[vector[vector[int]]] &p_
        )

        # Constructor with job ID and vector for processing times (creates shared_ptr internally)
        Job(const int &j_, const vector[vector[int]] &p_)

        # Parameterized constructor
        Job(
            const int &j_,
            const shared_ptr[vector[vector[int]]] &p_,
            const vector[vector[int]] &r_,
            const vector[vector[int]] &q_,
            const shared_ptr[vector[vector[vector[int]]]] &lat_,
            const shared_ptr[vector[int]] &m_,
            const int &s_
        )

        Job(
            const int &j_,
            const shared_ptr[vector[vector[int]]] &p_,
            const vector[vector[int]] &r_,
            const vector[vector[int]] &q_,
            const shared_ptr[vector[vector[vector[int]]]] &lat_,
            const shared_ptr[vector[int]] &m_
        )

        # Get T
        int get_T() const

    # Function to copy a job
    cdef shared_ptr[Job] copy_job(const shared_ptr[Job]& jobptr)

    # Function to copy a vector of jobs
    cdef vector[shared_ptr[Job]] copy_jobs(const vector[shared_ptr[Job]]& jobs)


ctypedef shared_ptr[Job] JobPtr


cdef extern from "sigma.hpp":

    cdef cppclass Sigma:
        shared_ptr[vector[int]] m
        vector[shared_ptr[Job]] jobs
        vector[vector[int]] C

        # Default constructor
        Sigma()

        # Constructor with empty instance
        Sigma(const shared_ptr[vector[int]] &m_)

        # Constructor with only jobs
        Sigma(const shared_ptr[vector[int]] &m_, const vector[shared_ptr[Job]] &jobs_)

        # Full constructor
        Sigma(const shared_ptr[vector[int]] &m_, const vector[shared_ptr[Job]] &jobs_, const vector[vector[int]] &C_)

        # Cost
        int cost() const

        # Job to bottom
        void job_to_bottom(const shared_ptr[Job] &job)

        # Job to top
        void job_to_top(const shared_ptr[Job] &job)


cdef extern from "permutation.hpp":

    cdef cppclass Permutation:
        # Attributes
        shared_ptr[vector[int]] m
        int n
        int level
        Sigma sigma1
        vector[shared_ptr[Job]] free_jobs
        Sigma sigma2

        # Default constructor
        Permutation()

        # Constructor from processing times
        Permutation(const vector[vector[vector[int]]] &p_)

        # Constructor from free jobs
        Permutation(const shared_ptr[vector[int]] &m_, const vector[shared_ptr[Job]] &jobs_)

        # Constructor given all desired attributes
        Permutation(const shared_ptr[vector[int]] &m_, const int &n_, const int &level_,
                    const Sigma &sigma1_, const vector[shared_ptr[Job]] &free_jobs_,
                    const Sigma &sigma2_)

        # Accessor methods
        vector[shared_ptr[Job]] *get_free_jobs()
        Sigma *get_sigma1()
        Sigma *get_sigma2()
        vector[shared_ptr[Job]] get_sequence() const
        vector[shared_ptr[Job]] get_sequence_copy() const
        vector[vector[int]] get_r() const
        vector[vector[int]] get_q() const

        # Modification methods
        void push_job(const int &j)
        void update_params()
        void front_updates()
        void back_updates()
        void compute_starts()

        # Feasibility check
        inline bool is_feasible()

        # Lower bound calculations
        int calc_lb_full()
        int calc_lb_1m()
        int calc_lb_2m()
        int calc_idle_time()

        inline int lower_bound_1m()
        inline int lower_bound_2m()

        # Deepcopy
        Permutation copy() const

        # Construction from reference
        emplace_from_ref_solution(const vector[shared_ptr[Job]] &ref_solution)

    # JobParams struct (if you need to use it from Cython)
    cdef struct JobParams:
        int t1
        int t2
        const int *p1
        const int *p2
        const int *lat

    # Two machine problem definition
    int two_mach_problem(const vector[shared_ptr[Job]] &jobs, const int &sl, const int &m1, const int &m2)

    # Makespan given ordered operations
    int two_mach_makespan(const vector[JobParams] &job_times)


cdef extern from "neh.hpp":

    cdef Permutation neh_constructive(vector[shared_ptr[Job]] &jobs)


cdef extern from "local_search.hpp":

    cdef Permutation local_search(vector[shared_ptr[Job]] &jobs)


cdef extern from "intensify.hpp":

    cdef Permutation intensify_ref(
        const Permutation &perm,
        const Permutation &ref_perm
    )
