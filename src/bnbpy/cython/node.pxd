# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool

import copy

from bnbpy.cython.counter cimport Counter
from bnbpy.cython.problem cimport Problem
from bnbpy.cython.solution cimport Solution


cdef class Node:

    cdef public:
        Problem problem
        Node parent
        int level
        double lb
        list[Node] children
        int _sort_index

    cdef:
        Counter _counter

    cdef void cleanup(Node self)

    cdef inline Solution get_solution(Node self):
        return self.problem.solution

    cdef inline int get_index(Node self):
        return self._sort_index

    cpdef void compute_bound(Node self)

    cpdef bool check_feasible(Node self)

    cpdef void set_solution(Node self, Solution solution)

    cdef inline void fathom(Node self):
        """Sets solution status of node as 'FATHOMED'"""
        self.solution.fathom()

    cpdef Node copy(self, bool deep=*)

    cdef inline Node deep_copy(Node self):
        return copy.deepcopy(self)

    cpdef list[Node] branch(Node self)

    cdef Node child_problem(Node self, Problem problem)

    cdef Node shallow_copy(Node self)


cdef Node init_node(Problem problem, Node parent=*)
