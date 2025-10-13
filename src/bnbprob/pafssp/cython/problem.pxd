# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.string cimport string

from bnbprob.pafssp.cpp.environ cimport (
    Permutation,
    local_search,
    neh_constructive,
    quick_constructive,
    intensification
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

    cdef inline void set_perm(PermFlowShop self, Permutation perm):
        self.perm = perm

    cdef inline Permutation get_perm(PermFlowShop self):
        return self.perm

    cpdef object get_mach_graph(PermFlowShop self)

    cdef void ccleanup(PermFlowShop self)

    cpdef PermFlowShop warmstart(PermFlowShop self)

    cpdef PermFlowShop quick_constructive(PermFlowShop self)

    cpdef PermFlowShop neh_constructive(PermFlowShop self)

    cpdef PermFlowShop local_search(PermFlowShop self)

    cpdef PermFlowShop randomized_heur(PermFlowShop self, int n_iter, unsigned int seed=*)

    cpdef PermFlowShop intensification(PermFlowShop self)

    cpdef PermFlowShop intensification_ref(
        PermFlowShop self,
        PermFlowShop reference
    )

    cpdef double calc_bound(PermFlowShop self)

    cpdef bool is_feasible(PermFlowShop self)

    cpdef list[PermFlowShop] branch(PermFlowShop self)

    cdef PermFlowShop _child_push(PermFlowShop self, int& j)

    cpdef void simple_bound_upgrade(PermFlowShop self)

    cpdef void bound_upgrade(PermFlowShop self)

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

    cdef inline PermFlowShop fast_copy(PermFlowShop self):
        cdef:
            PermFlowShop child
        child = type(self).__new__(type(self))
        child.solution = Solution()
        child.constructive = self.constructive
        return child

    cpdef void perm_copy(PermFlowShop self)


cdef class PermFlowShop2M(PermFlowShop):

    cpdef double calc_bound(PermFlowShop2M self)
