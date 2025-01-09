# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libc.math cimport INFINITY

from bnbpy.cython.node cimport Node

from typing import Optional

from bnbpy.solution import Solution


cdef:
    double LARGE_POS = INFINITY
    double LOW_NEG = -INFINITY
    int LARGE_INT = 100000000


cdef class BranchAndBound:
    """Class for solving optimization problems via Branch & Bound"""

    cdef public:
        object problem
        Node root
        double gap
        object queue
        double rtol
        double atol
        int explored
        object eval_node
        bool eval_in
        bool eval_out
        bool save_tree
        Node incumbent
        Node bound_node
        object __logger

    cdef double get_ub(BranchAndBound self)

    cdef double get_lb(BranchAndBound self)

    cdef object get_solution(BranchAndBound self)

    cpdef void _set_problem(BranchAndBound self, problem: Problem)

    cpdef void _restart_search(BranchAndBound self)

    cdef void _do_iter(BranchAndBound self, Node node)

    cpdef void enqueue(BranchAndBound self, Node node)

    cpdef Node dequeue(BranchAndBound self)

    cpdef void _warmstart(BranchAndBound self, solution: Optional[Solution])

    cpdef void branch(BranchAndBound self, Node node)

    cpdef void fathom(BranchAndBound self, Node node)

    cpdef void pre_eval_callback(BranchAndBound self, Node node)

    cpdef void post_eval_callback(BranchAndBound self, Node node)

    cpdef void enqueue_callback(BranchAndBound self, Node node)

    cpdef void dequeue_callback(BranchAndBound self, Node node)

    cpdef void solution_callback(BranchAndBound self, Node node)

    cpdef void _solve_root(BranchAndBound self)

    cpdef void _node_eval(BranchAndBound self, Node node)

    cpdef void _feasibility_check(BranchAndBound self, Node node)

    cpdef void set_solution(BranchAndBound self, Node node)

    cdef void _enqueue_core(BranchAndBound self, Node node)

    cdef Node _dequeue_core(BranchAndBound self)

    cdef bool _check_termination(BranchAndBound self, int maxiter)

    cdef void _update_bound(BranchAndBound self)

    cpdef void _log_headers(BranchAndBound self)

    cpdef void log_row(BranchAndBound self, object message)

    cdef void _update_gap(BranchAndBound self)

    cdef bool _optimality_check(BranchAndBound self)
