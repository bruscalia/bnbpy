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
from bnbprob.pfssp.cython.solution cimport FlowSolution
from bnbpy.cython.counter cimport Counter
from bnbpy.cython.problem cimport Problem


cdef class PermFlowShop(Problem):

    cdef public:
        string constructive
        # Cannot override attribute `solution` in cdef class
        # due to Cython limitation

    cdef inline FlowSolution get_solution(PermFlowShop self):
        return <FlowSolution>self.solution

    cdef void ccleanup(PermFlowShop self)

    cpdef FlowSolution warmstart(PermFlowShop self)

    cpdef FlowSolution quick_constructive(PermFlowShop self)

    cpdef FlowSolution neh_constructive(PermFlowShop self)

    cpdef FlowSolution ils(PermFlowShop self, int max_iter=*)

    cpdef FlowSolution randomized_heur(
        PermFlowShop self,
        int n_iter=*,
        unsigned int seed=*
    )

    cpdef FlowSolution local_search(PermFlowShop self)

    cpdef FlowSolution intensification(PermFlowShop self)

    cpdef FlowSolution intensification_ref(
        PermFlowShop self,
        FlowSolution ref_solution
    )

    cpdef FlowSolution path_relinking(
        PermFlowShop self,
        FlowSolution ref_solution
    )

    cpdef double calc_bound(PermFlowShop self)

    cpdef bool is_feasible(PermFlowShop self)

    cpdef list[PermFlowShop] branch(PermFlowShop self)

    cdef PermFlowShop _child_push(PermFlowShop self, int& j)

    cpdef void bound_upgrade(PermFlowShop self)

    cpdef int calc_idle_time(PermFlowShop self)

    cpdef PermFlowShop copy(PermFlowShop self, bool deep=*)

    cdef PermFlowShop _copy(PermFlowShop self)


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
