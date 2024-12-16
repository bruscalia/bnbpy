# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool

from typing import List, Literal, Optional

from bnbprob.pfssp.cython.heuristics cimport (
    local_search as ls,
    neh_constructive as neh,
    quick_constructive as qc,
)
from bnbprob.pfssp.cython.permutation cimport Permutation
from bnbprob.pfssp.cython.solution import FlowSolution


cdef class PermFlowShop:

    cdef public:
        object solution
        str constructive

    cpdef void cleanup(PermFlowShop self)

    cpdef void compute_bound(PermFlowShop self)

    cpdef bool check_feasible(PermFlowShop self)

    cpdef void set_solution(PermFlowShop self, object solution)

    cpdef int calc_bound(PermFlowShop self)

    cpdef bool is_feasible(PermFlowShop self)

    cpdef list[PermFlowShop] branch(PermFlowShop self)

    cdef PermFlowShop _child_push(PermFlowShop self, int j)

    cpdef PermFlowShop copy(PermFlowShop self)
