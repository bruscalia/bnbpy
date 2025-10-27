# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libc.math cimport INFINITY
from libcpp cimport bool
from libcpp.string cimport string

from typing import Optional

from bnbpy.cython.node cimport Node
from bnbpy.cython.priqueue cimport BasePriQueue
from bnbpy.cython.problem cimport Problem
from bnbpy.cython.solution cimport Solution


cdef extern from "limits.h":
    unsigned long long ULLONG_MAX


cdef:
    double LARGE_POS = INFINITY
    double LOW_NEG = -INFINITY


cdef class SearchResults:
    cdef public:
        Solution solution
        Problem problem


cdef class BranchAndBound:
    """Class for solving optimization problems via Branch & Bound"""

    cdef public:
        Problem problem
        Node root
        double gap
        BasePriQueue queue
        double rtol
        double atol
        unsigned long long explored
        string eval_node
        bool eval_in
        bool eval_out
        bool save_tree
        Node incumbent
        Node bound_node
        object __logger

    cdef double get_ub(BranchAndBound self)

    cdef double get_lb(BranchAndBound self)

    cdef Solution get_solution(BranchAndBound self)

    cdef void _set_problem(BranchAndBound self, Problem problem)

    cdef void _restart_search(BranchAndBound self)

    cdef void _do_iter(BranchAndBound self, Node node)

    cpdef void enqueue(BranchAndBound self, Node node)

    cpdef Node dequeue(BranchAndBound self)

    cpdef void _warmstart(BranchAndBound self, Problem warmstart_problem)

    cpdef void branch(BranchAndBound self, Node node)

    cpdef void fathom(BranchAndBound self, Node node)

    cpdef void pre_eval_callback(BranchAndBound self, Node node)

    cpdef void post_eval_callback(BranchAndBound self, Node node)

    cpdef void enqueue_callback(BranchAndBound self, Node node)

    cpdef void dequeue_callback(BranchAndBound self, Node node)

    cpdef void solution_callback(BranchAndBound self, Node node)

    cpdef void _enqueue_root(BranchAndBound self, Problem problem)

    cpdef void _node_eval(BranchAndBound self, Node node)

    cpdef void _feasibility_check(BranchAndBound self, Node node)

    cpdef void set_solution(BranchAndBound self, Node node)

    cdef void _enqueue_core(BranchAndBound self, Node node)

    cdef Node _dequeue_core(BranchAndBound self)

    cdef bool _check_termination(BranchAndBound self, unsigned long long maxiter)

    cdef void _update_bound(BranchAndBound self)

    cpdef void _log_headers(BranchAndBound self)

    cpdef void log_row(BranchAndBound self, object message)

    cdef void _update_gap(BranchAndBound self)

    cdef bool _optimality_check(BranchAndBound self)
