# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool

import copy
import itertools
from typing import List, Optional

from bnbprob.pfssp.cython.problem cimport PermFlowShop
from bnbprob.pfssp.cython.solution cimport FlowSolution


cdef class Node:

    cdef public:
        PermFlowShop problem
        Node parent
        int level
        double lb
        list[Node] children
        int _sort_index
        object _counter

    cpdef void cleanup(self)

    cpdef void compute_bound(Node self)

    cpdef bool check_feasible(Node self)

    cpdef void set_solution(Node self, FlowSolution solution)

    cpdef void fathom(Node self)

    cpdef list[Node] branch(Node self)

    cpdef Node child_problem(Node self, PermFlowShop problem)

    cpdef Node shallow_copy(Node self)
