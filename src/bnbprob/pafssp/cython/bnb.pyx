# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

from libc.math cimport sqrt
from libcpp cimport bool
from libcpp.vector cimport vector

from bnbprob.pafssp.cython.problem cimport BenchPermFlowShop, PermFlowShop
from bnbpy.cython.cbfs cimport CycleQueue, CycleLevel
from bnbpy.cython.node cimport Node
from bnbpy.cython.priqueue_cpp cimport CppPriorityQueue, DfsCppPriQueue, BestCppPriQueue
from bnbpy.cython.search cimport BranchAndBound, SearchResults
from bnbpy.cython.solution cimport Solution

cdef:
    int HEUR_BASE = 100


EVAL_NODE: str = "in"


cdef class DfsFlowShop(DfsCppPriQueue):

    cpdef vector[double] make_priority(self, Node node):
        cdef:
            int idle_time
            PermFlowShop problem

        problem = node.problem
        idle_time = problem.calc_idle_time()
        return [-node.level, node.lb, idle_time]


cdef class BestFirstFlowShop(BestCppPriQueue):

    cpdef vector[double] make_priority(self, Node node):
        cdef:
            int idle_time
            PermFlowShop problem

        problem = node.problem
        idle_time = problem.calc_idle_time()
        return [node.lb, idle_time]


cdef class CycleBestFlowShop(CycleQueue):
    """Cycle Best First Search node manager specialised for PermFlowShop,
    using :class:`DfsFlowShop`
    as the per-level priority queue.
    """

    def __init__(
        self,
        int max_size=1_000_000,
        bool permanent_fallback=False,
    ):
        super(CycleBestFlowShop, self).__init__(max_size, permanent_fallback)

    cpdef CycleLevel new_level(self, int level):
        cdef CycleLevel lvl
        lvl = CycleLevel(level)
        lvl.set_queue(DfsFlowShop())
        return lvl


cdef class LazyBnB(BranchAndBound):

    def __init__(
        self,
        PermFlowShop problem,
        save_tree=False,
        delay_lb5=False,
    ):
        super(LazyBnB, self).__init__(
            problem,
            EVAL_NODE,
            save_tree,
            None,
        )
        self.manager = DfsFlowShop()
        self.delay_lb5 = delay_lb5
        if delay_lb5:
            self.min_lb5_level = (problem.get_n() // 3) + 1
        else:
            self.min_lb5_level = 0


    @staticmethod
    def delay_by_root(problem: PermFlowShop) -> bool:
        lb1 = problem.calc_lb_1m()
        lb5 = problem.calc_lb_2m()
        return lb1 <= lb5

    cpdef void post_eval_callback(self, Node node):
        # Here the r and q values are not yet updated
        if node.lb < self.get_ub():
            # Update lower r and q values and recompute bound 1M
            node.c_upgrade_bound()
            # Delayed two machine bound upgrade
            if node.level < self.min_lb5_level and self.delay_lb5:
                return
            if node.lb < self.get_ub():
                # Two machine bound upgrade
                node.c_upgrade_bound()


cdef class CutoffBnB(LazyBnB):

    cdef public:
        float ub_value

    def __init__(
        self,
        PermFlowShop problem,
        float ub_value,
        save_tree=False,
        delay_lb5=False,
    ):
        super(CutoffBnB, self).__init__(
            problem,
            save_tree,
            delay_lb5,
        )
        self.manager = DfsFlowShop()
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
        problem.set_solution(solution)
        node = Node(problem)

        self.incumbent = node
        self.bound_node = None
        self.gap = 1.0
        self.manager.clear()


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
        self.manager.clear()

    cpdef void post_eval_callback(self, Node node):
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
        PermFlowShop problem,
        save_tree=False,
        delay_lb5=False,
        heur_factor=HEUR_BASE,
    ):
        super(CallbackBnB, self).__init__(
            problem,
            save_tree,
            delay_lb5,
        )
        self.manager = DfsFlowShop()
        self.base_heur_factor = heur_factor
        self.heur_factor = heur_factor
        self.heur_calls = 0

    cpdef void solution_callback(self, Node node):
        self.primal_heuristic(node)

    cpdef void dequeue_callback(self, Node node):
        if self.explored >= self.heur_factor:
            self.intensify(node)

    cpdef void intensify(self, Node node):
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
