# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libc.math cimport sqrt

import heapq
from typing import Optional, Union

from bnbprob.pafssp.cython.problem cimport BenchPermFlowShop, PermFlowShop
from bnbpy.cython.mod_queue cimport CycleQueue
from bnbpy.cython.node cimport Node
from bnbpy.cython.priqueue cimport DFSPriQueue, HeapPriQueue, NodePriQueue
from bnbpy.cython.search cimport BranchAndBound, SearchResults
from bnbpy.cython.solution cimport Solution

cdef:
    int HEUR_BASE = 100


EVAL_NODE: str = "in"


cdef class DFSPriQueueFS(HeapPriQueue):
    cpdef void enqueue(self, Node node):
        cdef:
            int idle_time
            PermFlowShop problem
        problem = node.problem
        idle_time = problem.calc_idle_time()
        heapq.heappush(
            self._queue,
            NodePriQueue((-node.level, node.lb, idle_time), node)
        )


cdef class LazyBnB(BranchAndBound):

    def __init__(
        self,
        rtol=0.0001,
        atol=0.0001,
        save_tree=False,
        delay_lb5=False
    ):
        super(LazyBnB, self).__init__(rtol, atol, EVAL_NODE, save_tree)
        self.queue = DFSPriQueueFS()
        self.delay_lb5 = delay_lb5
        self.min_lb5_level = 0

    @staticmethod
    def delay_by_root(problem: PermFlowShop) -> bool:
        lb1 = problem.calc_lb_1m()
        lb5 = problem.calc_lb_2m()
        return lb1 <= lb5

    def solve(
        LazyBnB self,
        PermFlowShop problem,
        maxiter: Optional[int] = None,
        timelimit: Optional[Union[int, float]] = None
    ) -> SearchResults:
        if self.delay_lb5:
            self.min_lb5_level = (problem.get_n() // 3) + 1
        else:
            self.min_lb5_level = 0
        return super(LazyBnB, self).solve(problem, maxiter, timelimit)

    cpdef void post_eval_callback(LazyBnB self, Node node):
        cdef:
            PermFlowShop problem
        # Here the r and q values are not yet updated
        if node.lb < self.get_ub():
            problem = node.problem
            # Update lower r and q values and recompute bound
            problem.simple_bound_upgrade()
            node.lb = problem.get_lb()
            # Delayed two machine bound upgrade
            if node.level < self.min_lb5_level and self.delay_lb5:
                return
            if node.lb < self.get_ub():
                # Two machine bound upgrade
                problem.double_bound_upgrade()
                node.lb = problem.get_lb()


cdef class CutoffBnB(LazyBnB):

    cdef public:
        float ub_value

    def __init__(
        self,
        float ub_value,
        rtol=0.0001,
        atol=0.0001,
        save_tree=False,
        delay_lb5=False
    ):
        super(CutoffBnB, self).__init__(rtol, atol, save_tree, delay_lb5)
        self.queue = DFSPriQueueFS()
        self.ub_value = ub_value

    cdef void _restart_search(CutoffBnB self):
        cdef:
            Node node
            Solution solution
            PermFlowShop problem

        solution = Solution()
        solution.set_lb(self.ub_value)
        solution.set_feasible()
        problem = PermFlowShop.__new__(PermFlowShop)
        problem.solution = solution
        node = Node(problem)

        self.incumbent = node
        self.bound_node = None
        self.gap = 1.0
        self.queue.clear()


cdef class BenchCutoffBnB(CutoffBnB):

    cdef void _restart_search(BenchCutoffBnB self):
        cdef:
            Node node
            Solution solution
            BenchPermFlowShop problem

        solution = Solution()
        solution.set_lb(self.ub_value)
        solution.set_feasible()
        problem = BenchPermFlowShop.__new__(BenchPermFlowShop)
        problem.solution = solution
        node = Node(problem)

        self.incumbent = node
        self.bound_node = None
        self.gap = 1.0
        self.queue.clear()

    cpdef void post_eval_callback(BenchCutoffBnB self, Node node):
        cdef:
            BenchPermFlowShop problem
        # Here the r and q values are assumed to be already updated
        if node.lb < self.get_ub():
            # Two machine bound upgrade
            problem = node.problem
            problem.double_bound_upgrade()
            node.lb = problem.get_lb()


cdef class CallbackBnB(LazyBnB):

    def __init__(
        self,
        rtol=0.0001,
        atol=0.0001,
        save_tree=False,
        delay_lb5=False,
        heur_factor=HEUR_BASE
    ):
        super(CallbackBnB, self).__init__(rtol, atol, save_tree, delay_lb5)
        self.queue = DFSPriQueueFS()
        self.base_heur_factor = heur_factor
        self.heur_factor = heur_factor
        self.heur_calls = 0

    cpdef void solution_callback(CallbackBnB self, Node node):
        cdef:
            PermFlowShop problem, ref_problem
            PermFlowShop new_prob
            Solution new_sol

        problem = node.problem
        new_prob = problem.local_search()
        if new_prob is not None:
            new_sol = new_prob.solution
            # General procedure in case is valid
            if new_prob.is_feasible() and new_sol.lb < node.lb:
                node.problem = new_prob
                node.set_solution(new_sol)
                node.check_feasible()
                self.set_solution(node)

    cpdef Node dequeue(CallbackBnB self):
        cdef:
            DFSPriQueueFS queue
            Node node

        node = self.queue.dequeue()
        if self.explored >= self.heur_factor:
            self.intensify(node)
        return node

    cpdef void intensify(CallbackBnB self, Node node):
        cdef:
            Node new_node
            PermFlowShop problem, ref_problem, new_prob

        if self.incumbent is None or self.explored < 1:
            return

        problem = node.problem
        # Sort free jobs according to
        # corresponding order in incumbent solution
        ref_problem = self.incumbent.problem
        new_prob = problem.intensify(ref_problem)
        if new_prob.solution.lb < self.get_ub():
            new_node = Node(new_prob)
            self.log_row("Intensification")
            self.set_solution(new_node)
            # Reduce the heuristic wait iterations factor
            self.heur_calls = <int>sqrt(self.heur_calls)
        else:
            self.heur_calls += 1
        self.heur_factor = (
            self.explored + self.base_heur_factor * self.heur_calls
        )
