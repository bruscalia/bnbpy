# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.deque cimport deque


cdef extern from "job.hpp":

    cdef cppclass Job:
        int j
        vector[int] p
        vector[int] r
        vector[int] q
        vector[vector[int]] lat

        # Declare the constructors
        # Default constructor
        Job()

        # Constructor with job ID, processing times, and MachineGraph
        Job(
            const int &j_,
            const vector[int] &p_,
            const MachineGraph &mach_graph
        )

        # Parameterized constructor
        Job(
            const int &j_,
            const vector[int] &p_,
            const vector[int] &r_,
            const vector[int] &q_,
            const vector[vector[int]] &lat_
        )

        # Get slope
        int get_slope() const

        # Get T
        int get_T() const

        # Recompute only r and q for the job given machine graph
        void recompute_r_q(const MachineGraph &mach_graph)


# Jobs are never mutated once built (owned by InstanceData)
ctypedef const Job* JobPtr


cdef extern from "sigma.hpp":

    cdef cppclass Sigma:
        int m
        vector[int] C
        const MachineGraph* mach_graph

        # Default constructor
        Sigma()

        # Constructor with empty instance and MachineGraph
        Sigma(const int &m_, const MachineGraph* mach_graph_)

        # Constructor with jobs and MachineGraph (from JobPtr vector)
        Sigma(const int &m_, const vector[JobPtr] &jobs_, const MachineGraph* mach_graph_)

        # Full constructor (from JobPtr vector)
        Sigma(const int &m_, const vector[JobPtr] &jobs_, const vector[int] &C_, const MachineGraph* mach_graph_)

        # Push job to the bottom of the sequence
        void job_to_bottom(JobPtr job)

        # Push job to the top of the sequence
        void job_to_top(JobPtr job)

        # Get jobs as JobPtr vector
        inline vector[JobPtr] get_jobs() const

        # Get number of jobs
        inline size_t n_jobs() const

        # Get machine graph
        MachineGraph get_mach_graph() const


cdef extern from "job_times.hpp":
    cdef cppclass JobTimes:
        int t1
        int t2
        int p1
        int p2
        int lat
        int j

        JobTimes(const int& t1_, const int& t2_, const int& p1_, const int& p2_,
                 const int& lat_, const int& j_)

        JobTimes(const int& m1, const int& m2, const Job& job_)


cdef extern from "mach_graph.hpp":
    cdef cppclass MachineGraph:
        # Default constructor
        MachineGraph()

        # All arguments constructor
        MachineGraph(
            int M,
            const vector[vector[int]]& prec,
            const vector[vector[int]]& succ,
            const vector[int]& topo_order,
            const vector[int]& rev_topo_order,
            const vector[vector[int]]& descendants
        )

        # Constructor without reverse topological order (computes it automatically)
        MachineGraph(
            int M,
            const vector[vector[int]]& prec,
            const vector[vector[int]]& succ,
            const vector[int]& topo_order,
            const vector[vector[int]]& descendants
        )

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
        TwoMach(const MachineGraph& mach_graph, const vector[JobPtr]& jobs)

        const vector[JobTimes]& get_seq(const int& m1, const int& m2) const


cdef extern from "instance_data.hpp":
    cdef cppclass InstanceData:
        InstanceData(
            const vector[vector[int]]& p,
            MachineGraph mach_graph
        ) except +
        int get_n() const
        int get_m() const
        const MachineGraph& get_mach_graph() const
        const vector[JobPtr]& get_jobs() const


cdef extern from "permutation.hpp":

    cdef cppclass Permutation:
        int m
        int n
        int level
        Sigma sigma1
        vector[JobPtr] free_jobs
        Sigma sigma2
        const InstanceData* instance

        # Default constructor (no instance; placeholder only)
        Permutation()

        # Root node: all jobs of the instance are free
        Permutation(const InstanceData* instance_)

        # Given jobs are free and nothing is scheduled
        Permutation(
            const InstanceData* instance_,
            const vector[JobPtr]& free_jobs_
        )

        # Constructor given all desired attributes
        Permutation(
            const InstanceData* instance_,
            int level_,
            const Sigma& sigma1_,
            const vector[JobPtr]& free_jobs_,
            const Sigma& sigma2_
        )

        # Accessor methods
        vector[JobPtr] get_free_jobs() const
        Sigma get_sigma1() const
        Sigma get_sigma2() const
        vector[JobPtr] get_sequence() const
        vector[int] get_r() const
        vector[int] get_q() const
        const MachineGraph& get_mach_graph() const
        const InstanceData* get_instance() const

        # Modification methods
        void push_job(const unsigned int &j)
        void update_params()

        # Start times aligned with get_sequence(); does not mutate jobs
        vector[vector[int]] compute_starts() const

        # Feasibility check
        inline bool is_feasible() const

        # Lower bound calculations
        inline int calc_lb_1m()
        inline int calc_lb_2m()
        int calc_lb_full()
        int lower_bound_1m()
        int lower_bound_2m()
        int calc_idle_time()
        int calc_tot_time()

        # Additional methods
        void emplace_from_ref_solution(const vector[JobPtr]& ref_solution)


cdef extern from "local_search.hpp":

    cdef Permutation local_search(
        vector[JobPtr]& jobs_,
        const InstanceData& inst
    )


cdef extern from "neh.hpp":

    cdef Permutation neh_initialization(
        vector[JobPtr]& jobs,
        const InstanceData& inst
    )


cdef extern from "randomized_heur.hpp":

    cdef Permutation randomized_heur(
        vector[JobPtr] jobs_,
        int n_iter,
        unsigned int seed,
        const InstanceData& inst
    )


cdef extern from "iga.hpp":

    cdef Permutation iga(
        vector[JobPtr]& jobs_,
        const InstanceData& inst,
        const int& max_iter,
        const int& d,
        const int& seed
    )


cdef extern from "quick_constructive.hpp":

    cdef Permutation quick_constructive(
        vector[JobPtr]& jobs,
        const InstanceData& inst
    )


cdef extern from "intensify.hpp":

    cdef Permutation intensify(
        const Permutation &perm,
        const Permutation &ref_perm
    )
