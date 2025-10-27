# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.string cimport string
from libcpp.vector cimport vector

from bnbprob.pafssp.cpp.environ cimport (
    MachineGraph,
    Permutation,
    iga,
    intensify,
    local_search,
    neh_initialization,
    quick_constructive
)
from bnbprob.pafssp.cpp.environ cimport Permutation
from bnbprob.pafssp.cython.pyjob cimport PyJob, job_to_py
from bnbpy.cython.problem cimport Problem
from bnbpy.cython.solution cimport Solution


cdef class PermFlowShop(Problem):

    cdef public:
        string constructive
        # Cannot override attribute `solution` in cdef class
        # due to Cython limitation

    cdef:
        Permutation perm

    cdef inline void set_perm(PermFlowShop self, vector[vector[int]] p_, MachineGraph mach_graph_):
        self.perm = Permutation(p_, mach_graph_)

    cdef inline Permutation get_perm(PermFlowShop self):
        return self.perm

    cdef inline int get_n(PermFlowShop self):
        return self.perm.n

    cpdef object get_mach_graph(PermFlowShop self)

    cdef void ccleanup(PermFlowShop self)

    cpdef PermFlowShop warmstart(PermFlowShop self)

    cpdef PermFlowShop quick_constructive(PermFlowShop self)

    cpdef PermFlowShop neh_initialization(PermFlowShop self)

    cpdef PermFlowShop multistart_initialization(PermFlowShop self)

    cpdef PermFlowShop iga_initialization(PermFlowShop self)

    cpdef PermFlowShop local_search(PermFlowShop self)

    cpdef PermFlowShop randomized_heur(PermFlowShop self, int n_iter, unsigned int seed=*)

    cpdef PermFlowShop iga_heur(PermFlowShop self, int n_iter, int d, unsigned int seed=*)

    cpdef PermFlowShop intensify(
        PermFlowShop self,
        PermFlowShop reference
    )

    cpdef double calc_bound(PermFlowShop self)

    cpdef bool is_feasible(PermFlowShop self)

    cpdef list[PermFlowShop] branch(PermFlowShop self)

    cdef PermFlowShop _child_push(PermFlowShop self, int& j)

    cpdef void simple_bound_upgrade(PermFlowShop self)

    cpdef void double_bound_upgrade(PermFlowShop self)

    cdef void _double_bound_upgrade(PermFlowShop self)

    cpdef int calc_lb_1m(PermFlowShop self)

    cpdef int calc_lb_2m(PermFlowShop self)

    cpdef int lower_bound_1m(PermFlowShop self)

    cpdef int lower_bound_2m(PermFlowShop self)

    cpdef void update_params(PermFlowShop self)

    cpdef void push_job(PermFlowShop self, int& j)

    cdef void _push_job(PermFlowShop self, int& j)

    cpdef void compute_starts(PermFlowShop self)

    cpdef int calc_idle_time(PermFlowShop self)

    cpdef int calc_tot_time(PermFlowShop self)

    cpdef PermFlowShop copy(PermFlowShop self, bool deep=*)

    cdef PermFlowShop _copy(PermFlowShop self)

    cpdef void perm_copy(PermFlowShop self)


cdef class BenchPermFlowShop(PermFlowShop):

    cpdef double calc_bound(BenchPermFlowShop self)


cdef class PermFlowShop1M(PermFlowShop):

    cpdef double calc_bound(PermFlowShop1M self)

    cpdef void double_bound_upgrade(PermFlowShop1M self)
