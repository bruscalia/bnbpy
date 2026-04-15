# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libc.math cimport INFINITY
from libcpp cimport bool
from libcpp.string cimport string

from typing import Optional

from bnbpy.cython.manager cimport BaseNodeManager
from bnbpy.cython.node cimport Node
from bnbpy.cython.problem cimport Problem
from bnbpy.cython.solution cimport Solution


cdef:
    double LARGE_POS = INFINITY
    double LOW_NEG = -INFINITY


cdef class SearchResults:
    cdef public:
        Solution solution
        Problem problem


cdef class BranchAndBound:

    cdef public:
        double rtol
        double atol

    cdef readonly:
        Problem problem
        Node root
        double gap
        BaseNodeManager manager
        unsigned long long explored
        string eval_node
        bool eval_in
        bool eval_out
        bool save_tree
        Node incumbent
        Node bound_node

    cdef:
        object logger

    cdef double get_ub(BranchAndBound self)

    cdef double get_lb(BranchAndBound self)

    cdef Solution get_solution(BranchAndBound self)

    cpdef void set_manager(self, BaseNodeManager manager)

    cdef void _restart_search(BranchAndBound self)

    cpdef void reset(self)

    cdef void _do_iter(BranchAndBound self, Node node)

    cpdef void _warmstart(BranchAndBound self, Problem warmstart_problem)

    cpdef void branch(BranchAndBound self, Node node)

    cpdef void primal_heuristic(BranchAndBound self, Node node)

    cpdef void upgrade_bound(BranchAndBound self, Node node)

    cpdef void fathom(BranchAndBound self, Node node)

    cpdef void pre_eval_callback(BranchAndBound self, Node node)

    cpdef void post_eval_callback(BranchAndBound self, Node node)

    cpdef void enqueue_callback(BranchAndBound self, Node node)

    cpdef void dequeue_callback(BranchAndBound self, Node node)

    cpdef void solution_callback(BranchAndBound self, Node node)

    cpdef void _enqueue_root(BranchAndBound self)

    cpdef void _node_eval(BranchAndBound self, Node node)

    cpdef void _feasibility_check(BranchAndBound self, Node node)

    cpdef void set_solution(BranchAndBound self, Node node)

    cpdef void set_bound(BranchAndBound self, Node node)

    cdef void _enqueue_core(BranchAndBound self, Node node)

    cdef Node _dequeue_core(BranchAndBound self)

    cdef bool _check_termination(BranchAndBound self, unsigned long long maxiter)

    cdef void _update_bound(BranchAndBound self)

    cpdef void _log_headers(BranchAndBound self)

    cpdef void log_row(BranchAndBound self, object message)

    cdef void _update_gap(BranchAndBound self)

    cdef bool _optimality_check(BranchAndBound self)
