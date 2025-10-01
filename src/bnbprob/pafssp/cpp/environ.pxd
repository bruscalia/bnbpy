# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.memory cimport shared_ptr
from libcpp.unordered_set cimport unordered_set


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

        # Constructor with job ID, shared_ptr for processing times, and MachineGraph
        Job(
            const int &j_,
            const shared_ptr[vector[int]] &p_,
            const MachineGraph &mach_graph
        )

        # Constructor with job ID, vector for processing times, and MachineGraph
        Job(const int &j_, const vector[int] &p_, const MachineGraph &mach_graph)

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
        const MachineGraph* mach_graph

        # Default constructor
        Sigma()

        # Constructor with empty instance and MachineGraph
        Sigma(const int &m_, const MachineGraph* mach_graph_)

        # Constructor with empty instance and shared_ptr<MachineGraph>
        Sigma(const int &m_, const shared_ptr[MachineGraph] &mach_graph_)

        # Constructor with jobs and MachineGraph
        Sigma(const int &m_, const vector[shared_ptr[Job]] &jobs_, const MachineGraph* mach_graph_)

        # Full constructor with MachineGraph
        Sigma(const int &m_, const vector[shared_ptr[Job]] &jobs_, const vector[int] &C_, const MachineGraph* mach_graph_)

        # Push job to the bottom of the sequence
        void job_to_bottom(const shared_ptr[Job] &job)

        # Push job to the top of the sequence
        void job_to_top(const shared_ptr[Job] &job)

        # Get machine graph
        MachineGraph get_mach_graph() const


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


cdef extern from "mach_graph.hpp":
    cdef cppclass MachineGraph:
        # Default constructor
        MachineGraph()

        # All arguments constructor
        MachineGraph(int M,
                     const vector[vector[int]]& prec,
                     const vector[vector[int]]& succ,
                     const vector[int]& topo_order,
                     const vector[int]& rev_topo_order,
                     const vector[vector[int]]& descendants)

        # Constructor without reverse topological order (computes it automatically)
        MachineGraph(int M,
                     const vector[vector[int]]& prec,
                     const vector[vector[int]]& succ,
                     const vector[int]& topo_order,
                     const vector[vector[int]]& descendants)

        # Getters for precedence operations by index
        const vector[int]& get_prec(int machine_idx) const

        # Getters for successor operations by index
        const vector[int]& get_succ(int machine_idx) const

        # Getters for all successor operations
        const vector[vector[int]]& get_succ_all() const

        # Getters for all precedence operations
        const vector[vector[int]]& get_prec_all() const

        # Getter for topological order
        const vector[int]& get_topo_order() const

        # Getter for reverse topological order
        const vector[int]& get_rev_topo_order() const

        # Getter for descendants of machines
        const vector[vector[int]]& get_descendants() const

        # Getter for number of machines
        int get_M() const


cdef extern from "two_mach.hpp":
    cdef cppclass TwoMach:
        TwoMach()
        TwoMach(const int& m, const vector[JobPtr]& jobs)

        void erase_job(const JobPtr& job)
        const vector[JobTimes]& get_seq(const int& m1, const int& m2)


cdef extern from "permutation.hpp":

    cdef cppclass Permutation:
        int m
        int n
        int level
        Sigma sigma1
        vector[shared_ptr[Job]] free_jobs
        Sigma sigma2
        shared_ptr[MachineGraph] mach_graph

        # Default constructor
        Permutation()

        # Constructor from processing times
        Permutation(const vector[vector[int]]& p_,
                    const shared_ptr[MachineGraph]& mach_graph_)

        # Constructor from free jobs
        Permutation(const int &m_, const vector[shared_ptr[Job]] &jobs_,
                    const shared_ptr[MachineGraph]& mach_graph_)

        # Constructor given all desired attributes
        Permutation(
            const int &m_, const int &n_, const int &level_,
            const Sigma &sigma1_, const vector[shared_ptr[Job]] &free_jobs_,
            const Sigma &sigma2_,
            const shared_ptr[MachineGraph]& mach_graph_,
            const shared_ptr[TwoMach]& two_mach_cache_
        )

        # Constructor given all desired attributes but two_mach
        Permutation(
            const int &m_, const int &n_, const int &level_,
            const Sigma &sigma1_, const vector[shared_ptr[Job]] &free_jobs_,
            const Sigma &sigma2_,
            const shared_ptr[MachineGraph]& mach_graph_
        )

        # Constructor from processing times with MachineGraph object
        Permutation(const vector[vector[int]]& p_,
                    const MachineGraph& mach_graph_)

        # Constructor from free jobs with MachineGraph object
        Permutation(const int &m_, const vector[shared_ptr[Job]] &jobs_,
                    const MachineGraph& mach_graph_)

        # Constructor given all desired attributes with MachineGraph object
        Permutation(
            const int &m_, const int &n_, const int &level_,
            const Sigma &sigma1_, const vector[shared_ptr[Job]] &free_jobs_,
            const Sigma &sigma2_, const MachineGraph& mach_graph_,
            const shared_ptr[TwoMach]& two_mach_cache_
        )

        # Constructor given all desired attributes but two_mach with MachineGraph object
        Permutation(
            const int &m_, const int &n_, const int &level_,
            const Sigma &sigma1_, const vector[shared_ptr[Job]] &free_jobs_,
            const Sigma &sigma2_, const MachineGraph& mach_graph_
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
        vector[JobTimes*] get_job_times(const int& m1, const int& m2) const
        MachineGraph get_mach_graph() const

        # Modification methods
        void push_job(const int &j)
        void push_job_forward(const int &j)
        void push_job_backward(const int &j)
        void push_job_dyn(const int &j)
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
        int calc_tot_time()

        # Additional methods
        void emplace_from_ref_solution(const vector[shared_ptr[Job]]& ref_solution)

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
            const shared_ptr[MachineGraph]& mach_graph_,
            const shared_ptr[TwoMach]& two_mach_cache_,
            const unordered_set[int]& scheduled_jobs_
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

    cdef Permutation local_search(vector[JobPtr] &perm,
                                  const shared_ptr[MachineGraph]& mach_graph)


cdef extern from "neh.hpp":

    cdef Permutation neh_constructive(vector[shared_ptr[Job]] &jobs,
                                      const shared_ptr[MachineGraph]& mach_graph)


cdef extern from "quick_constructive.hpp":

    cdef Permutation quick_constructive(vector[shared_ptr[Job]] &jobs,
                                        const shared_ptr[MachineGraph]& mach_graph)


cdef extern from "intensify.hpp":

    cdef Permutation intensification(
        const Sigma &sigma1,
        const vector[shared_ptr[Job]] &jobs,
        const Sigma &sigma2,
        const shared_ptr[MachineGraph]& mach_graph
    )

    cdef Permutation intensify(
        const Sigma &sigma1,
        const vector[shared_ptr[Job]] &jobs,
        const Sigma &sigma2,
        const shared_ptr[MachineGraph]& mach_graph
    )

    cdef Permutation intensify(
        const Permutation &perm
    )

    cdef Permutation intensify_ref(
        const Permutation &perm,
        const Permutation &ref_perm
    )
