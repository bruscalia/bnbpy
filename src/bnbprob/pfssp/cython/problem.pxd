# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool

from typing import Optional

from bnbprob.pfssp.cpp.permutation cimport Permutation
from bnbprob.pfssp.cython.heuristics cimport (
    local_search as ls,
    neh_constructive as neh,
    quick_constructive as qc,
)
from bnbprob.pfssp.cython.solution cimport FlowSolution


cdef class PermFlowShop:

    cdef public:
        FlowSolution solution
        str constructive

    cpdef void cleanup(PermFlowShop self)

    cdef void ccleanup(PermFlowShop self)

    cpdef void compute_bound(PermFlowShop self)

    cpdef bool check_feasible(PermFlowShop self)

    cpdef void set_solution(PermFlowShop self, object solution)

    cpdef FlowSolution warmstart(PermFlowShop self)

    cpdef FlowSolution quick_constructive(PermFlowShop self)

    cpdef FlowSolution neh_constructive(PermFlowShop self)

    cpdef FlowSolution local_search(PermFlowShop self)

    cpdef int calc_bound(PermFlowShop self)

    cpdef bool is_feasible(PermFlowShop self)

    cpdef list[PermFlowShop] branch(PermFlowShop self)

    cdef PermFlowShop _child_push(PermFlowShop self, int& j)

    cpdef void bound_upgrade(PermFlowShop self)

    cpdef PermFlowShop copy(PermFlowShop self)

    cdef PermFlowShop _copy(PermFlowShop self)


cdef class PermFlowShop2M(PermFlowShop):

    cpdef int calc_bound(PermFlowShop2M self)
