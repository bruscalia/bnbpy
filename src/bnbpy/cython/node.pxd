# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool

import copy

from bnbpy.cython.counter cimport Counter
from bnbpy.cython.problem cimport Problem, P
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

    cdef void cleanup(self)

    cdef inline Solution get_solution(self):
        return self.problem.solution

    cdef inline int get_index(self):
        return self._sort_index

    cpdef void compute_bound(self)

    cpdef bool check_feasible(self)

    cpdef void set_solution(self, Solution solution)

    cdef inline void fathom(self):
        """Sets solution status of node as 'FATHOMED'"""
        self.solution.fathom()

    cpdef Node copy(self, bool deep=*)

    cdef inline Node deep_copy(self):
        return copy.deepcopy(self)

    cpdef list[Node] branch(self)

    cpdef Node primal_heuristic(self)

    cdef void c_upgrade_bound(self)

    cpdef void upgrade_bound(self)

    cdef Node child_problem(self, P problem)

    cdef Node shallow_copy(self)


cdef Node init_node(P problem, Node parent=*)
