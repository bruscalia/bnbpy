# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

# Declarations of the C++ classes and functions used by the Cython modules
# of bnbprob.pafssp (see the corresponding headers for the full API)

from libcpp cimport bool
from libcpp.vector cimport vector


cdef extern from "job.hpp":

    cdef cppclass Job:
        int j
        vector[int] p
        vector[int] r
        vector[int] q
        vector[vector[int]] lat


# Jobs are never mutated once built (owned by InstanceData)
ctypedef const Job* JobPtr


cdef extern from "sigma.hpp":

    cdef cppclass Sigma:
        int m
        vector[int] C

        # Get jobs as JobPtr vector
        inline vector[JobPtr] get_jobs() const


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


cdef extern from "instance_data.hpp":
    cdef cppclass InstanceData:
        InstanceData(
            const vector[vector[int]]& p,
            MachineGraph mach_graph
        ) except +
        int get_n() const
        int get_m() const
        const MachineGraph& get_mach_graph() const


cdef extern from "permutation.hpp":

    cdef cppclass Permutation:
        int n
        Sigma sigma1
        vector[JobPtr] free_jobs
        Sigma sigma2

        # Default constructor (no instance; placeholder only)
        Permutation()

        # Root node: all jobs of the instance are free
        Permutation(const InstanceData* instance_)

        # Accessor methods
        vector[JobPtr] get_free_jobs() const
        vector[JobPtr] get_sequence() const

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
