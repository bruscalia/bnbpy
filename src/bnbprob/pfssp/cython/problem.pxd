# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.string cimport string

from typing import Optional

from bnbprob.pfssp.cpp.environ cimport (
    Permutation,
    local_search,
    neh_constructive,
    quick_constructive,
    intensification
)
from bnbprob.pfssp.cpp.environ cimport Permutation
from bnbprob.pfssp.cython.pyjob cimport PyJob, job_to_py
from bnbpy.cython.counter cimport Counter
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

    cdef void ccleanup(PermFlowShop self)

    cpdef PermFlowShop warmstart(PermFlowShop self)

    cpdef PermFlowShop quick_constructive(PermFlowShop self)

    cpdef PermFlowShop neh_constructive(PermFlowShop self)

    cpdef PermFlowShop ils(
        PermFlowShop self,
        int max_iter=*,
        int max_age=*,
        int d=*,
        unsigned int seed=*
    )

    cpdef PermFlowShop randomized_heur(
        PermFlowShop self,
        int n_iter=*,
        unsigned int seed=*
    )

    cpdef PermFlowShop local_search(PermFlowShop self)

    cpdef PermFlowShop intensification(PermFlowShop self)

    cpdef PermFlowShop intensification_ref(
        PermFlowShop self,
        PermFlowShop reference
    )

    cpdef PermFlowShop path_relinking(
        PermFlowShop self,
        PermFlowShop reference
    )

    cpdef double calc_bound(PermFlowShop self)

    cpdef bool is_feasible(PermFlowShop self)

    cpdef list[PermFlowShop] branch(PermFlowShop self)

    cdef PermFlowShop _child_push(PermFlowShop self, int& j)

    cpdef void bound_upgrade(PermFlowShop self)

    cpdef int calc_lb_1m(PermFlowShop self)

    cpdef int calc_lb_2m(PermFlowShop self)

    cpdef int lower_bound_1m(PermFlowShop self)

    cpdef int lower_bound_2m(PermFlowShop self)

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


cdef class PermFlowShop2M(PermFlowShop):

    cpdef double calc_bound(PermFlowShop2M self)


cdef class PermFlowShopLevelCount(PermFlowShop):

    cdef public:
        object lb_counter

    cpdef void bound_upgrade(PermFlowShopLevelCount self)

    cpdef PermFlowShopLevelCount copy(PermFlowShopLevelCount self, bool deep=*)

    cdef PermFlowShopLevelCount _copy(PermFlowShopLevelCount self)


cdef class PermFlowShopQuit(PermFlowShop):

    cdef:
        bool do_lb5

    cpdef void bound_upgrade(PermFlowShopQuit self)

    cpdef PermFlowShopQuit copy(PermFlowShopQuit self, bool deep=*)

    cdef PermFlowShopQuit _copy(PermFlowShopQuit self)


cdef class UpgradeCounter:
    cdef public:
        Counter stay_two_mach
        Counter switch_to_single
        Counter stay_single
        Counter switch_to_two_mach


cdef class PermFlowShopCounter(PermFlowShopQuit):

    cdef public:
        UpgradeCounter upgrade_counter

    cpdef void bound_upgrade(PermFlowShopCounter self)

    cpdef PermFlowShopCounter copy(PermFlowShopCounter self, bool deep=*)

    cdef PermFlowShopCounter _copy(PermFlowShopCounter self)
