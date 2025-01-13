# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool

import copy
import itertools
from typing import List, Optional, Union

from bnbpy.problem import Problem
from bnbpy.solution import Solution


cdef class Node:

    cdef public:
        object problem
        Node parent
        int level
        double lb
        list[Node] children
        int _sort_index
        object _counter

    cdef void cleanup(Node self)

    cpdef void compute_bound(Node self)

    cpdef bool check_feasible(Node self)

    cpdef void set_solution(Node self, solution: Solution)

    cpdef void fathom(Node self)

    cpdef list[Node] branch(Node self)

    cdef Node child_problem(Node self, object problem)

    cpdef Node shallow_copy(Node self)
