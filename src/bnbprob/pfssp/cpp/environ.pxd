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
        Job()

        # Constructor with job ID and shared_ptr for processing times
        Job(
            const int &j_,
            const shared_ptr[vector[int]] &p_
        )

        # Constructor with job ID and vector for processing times (creates shared_ptr internally)
        Job(const int &j_, const vector[int] &p_)

        # Parameterized constructor
        Job(
            const int &j_,
            const shared_ptr[vector[int]] &p_,
            const vector[int] &r_,
            const vector[int] &q_,
            const shared_ptr[vector[vector[int]]] &lat_,
            const int &slope_,
            const int &T_
        )

        # Get glope
        int get_slope() const

        # Get T
        int get_T() const

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
        Sigma()

        # Constructor with empty instance
        Sigma(const int &m_)

        # Constructor with only jobs
        Sigma(const int &m_, const vector[shared_ptr[Job]] &jobs_)

        # Full constructor
        Sigma(const int &m_, const vector[shared_ptr[Job]] &jobs_, const vector[int] &C_)

        # Push job to the bottom of the sequence
        void job_to_bottom(const shared_ptr[Job] &job)

        # Push job to the top of the sequence
        void job_to_top(const shared_ptr[Job] &job)


cdef extern from "job_times.hpp":
    cdef cppclass JobTimes:
        int t1
        int t2
        const int* p1
        const int* p2
        const int* lat
        const Job* jobptr

        JobTimes(const int& t1_, const int& t2_, const int*& p1_, const int*& p2_,
                 const int*& lat_, const JobPtr& jobptr_)

        JobTimes(const int& t1_, const int& t2_, const int& p1_, const int& p2_,
                 const int& lat_, const JobPtr& jobptr_)

        JobTimes(const int& m1, const int& m2, const JobPtr& jobptr_)


cdef extern from "two_mach.hpp":
    cdef cppclass TwoMach:
        TwoMach()
        TwoMach(const int& m, const vector[JobPtr]& jobs)

        void erase_job(const JobPtr& job)
        vector[JobTimes] get_seq(const int& m1, const int& m2)


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
            const Sigma &sigma2_,
            const TwoMach &two_mach_cache_
        )

        # Accessor methods
        vector[shared_ptr[Job]] *get_free_jobs()
        Sigma *get_sigma1()
        Sigma *get_sigma2()
        vector[shared_ptr[Job]] get_sequence() const
        vector[shared_ptr[Job]] get_sequence_copy() const
        vector[shared_ptr[Job]] get_free_jobs_copy() const
        vector[int] get_r() const
        vector[int] get_q() const

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
        int calc_idle_time()

        # Copy method
        inline Permutation copy() const

        # Private constructor for copy method
        Permutation(
            int m_,
            int n_,
            int level_,
            const Sigma &sigma1_,
            vector[shared_ptr[Job]] &&free_jobs_,
            const Sigma &sigma2_,
            const TwoMach &two_mach_cache_
        )

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


cdef extern from "local_search.hpp":

    cdef Permutation local_search(vector[JobPtr] &perm)


cdef extern from "neh.hpp":

    cdef Permutation neh_constructive(vector[shared_ptr[Job]] &jobs)


cdef extern from "quick_constructive.hpp":

    cdef Permutation quick_constructive(vector[shared_ptr[Job]] &jobs)


cdef extern from "randomized_heur.hpp":

    cdef Permutation randomized_heur(
        vector[shared_ptr[Job]] &jobs,
        int n_iter,
        unsigned int seed
    )


cdef extern from "intensify.hpp":

    cdef Permutation intensification(
        const Sigma &sigma1,
        const vector[shared_ptr[Job]] &jobs,
        const Sigma &sigma2
    )

    cdef Permutation intensify(
        const Sigma &sigma1,
        const vector[shared_ptr[Job]] &jobs,
        const Sigma &sigma2
    )

    cdef Permutation intensify(
        const Permutation &perm
    )
