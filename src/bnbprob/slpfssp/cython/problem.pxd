# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.string cimport string

from typing import Optional

from bnbprob.slpfssp.cpp.environ cimport Permutation
from bnbprob.slpfssp.cython.solution cimport FlowSolution
from bnbpy.cython.problem cimport Problem


cdef class PermFlowShop(Problem):

    # Cannot override attribute `solution` in cdef class
    # due to Cython limitation

    cdef inline FlowSolution get_solution(PermFlowShop self):
        return <FlowSolution>self.solution

    cdef void ccleanup(PermFlowShop self)

    cpdef FlowSolution warmstart(PermFlowShop self)

    cpdef FlowSolution local_search(PermFlowShop self)

    cpdef FlowSolution intensification_ref(
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
