# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

import heapq
from libc.math cimport sqrt

from bnbprob.pafssp.cython.problem cimport PermFlowShop
from bnbpy.cython.mod_queue cimport CycleQueue
from bnbpy.cython.node cimport Node
from bnbpy.cython.priqueue cimport DFSPriQueue, HeapPriQueue, NodePriQueue
from bnbpy.cython.search cimport BranchAndBound
from bnbpy.cython.solution cimport Solution

cdef:
    int HEUR_BASE = 100
    int RESTART = 10_000


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


cdef class DFSPriQueueFSTrunc(HeapPriQueue):
    cdef:
        int trunc_index

    def __init__(self):
        super(DFSPriQueueFSTrunc, self).__init__()
        self.trunc_index = 0

    cpdef void enqueue(self, Node node):
        cdef:
            int idle_time
            PermFlowShop problem
        problem = node.problem
        idle_time = problem.calc_idle_time()
        heapq.heappush(
            self._queue,
            NodePriQueue(
                (self.trunc_index, node.lb, -node.level, idle_time), node
                # (self.trunc_index, -node.level, node.lb, idle_time), node
            )
        )

    cdef void next(self):
        self.trunc_index += 1

    cdef void reset(self):
        self.trunc_index = 0


cdef class LazyBnB(BranchAndBound):

    def __init__(
        self,
        rtol=0.0001,
        atol=0.0001,
        eval_node='in',
        save_tree=False,
        queue_mode='dfs',
    ):
        super(LazyBnB, self).__init__(rtol, atol, eval_node, save_tree)
        self.queue = self.queue_factory(queue_mode)

    @staticmethod
    def queue_factory(mode: str):
        if mode == 'cycle':
            return CycleQueue()
        elif mode == 'dfs':
            return DFSPriQueueFS()
        raise ValueError(f"Unknown queue mode: {mode}")

    cpdef void post_eval_callback(LazyBnB self, Node node):
        cdef:
            PermFlowShop problem
        if node.lb < self.get_ub():
            problem = node.problem
            problem.bound_upgrade()
            node.lb = problem.get_lb()


cdef class CutoffBnB(LazyBnB):

    cdef public:
        float ub_value

    def __init__(
        self,
        float ub_value,
        rtol=0.0001,
        atol=0.0001,
        eval_node='in',
        save_tree=False,
        queue_mode='dfs',
    ):
        super(CutoffBnB, self).__init__(rtol, atol, eval_node, save_tree)
        self.queue = self.queue_factory(queue_mode)
        self.ub_value = ub_value

    # cpdef void _warmstart(
    #     CutoffBnB self,
    #     Solution solution
    # ):
    #     return

    cdef inline void _restart_search(CutoffBnB self):
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


cdef class CallbackBnB(LazyBnB):

    def __init__(
        self,
        rtol=0.0001,
        atol=0.0001,
        eval_node='in',
        save_tree=False,
        queue_mode='dfs',
        heur_factor=HEUR_BASE
    ):
        super(CallbackBnB, self).__init__(rtol, atol, eval_node, save_tree)
        self.queue = self.queue_factory(queue_mode)
        self.base_heur_factor = heur_factor
        self.heur_factor = heur_factor
        self.heur_calls = 0
        self.level_restart = 0

    @staticmethod
    def queue_factory(mode: str):
        if mode == 'cycle':
            return CycleQueue()
        elif mode == 'dfs':
            return DFSPriQueueFS()
        raise ValueError(f"Unknown queue mode: {mode}")

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
        if (
            self.explored >= self.heur_factor or node is self.bound_node
        ):
            # pass
            self.intensify(node)
        return node

    cpdef void intensify(CallbackBnB self, Node node):
        cdef:
            Node new_node
            PermFlowShop problem, ref_problem, new_prob

        problem = node.problem
        if self.explored >= 1:
            # Sort free jobs according to
            # corresponding order in incumbent solution
            if self.incumbent is not None:
                ref_problem = self.incumbent.problem
                new_prob = problem.intensification_ref(ref_problem)
            else:
                new_prob = problem.intensification()
            # new_sol = problem.intensification()
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


cdef class TruncateBnB(CallbackBnB):
    def __init__(
        self,
        rtol=0.0001,
        atol=0.0001,
        eval_node='in',
        save_tree=False,
        queue_mode='dfs',
        heur_factor=HEUR_BASE,
    ):
        super(TruncateBnB, self).__init__(
            rtol, atol, eval_node, save_tree, queue_mode, heur_factor
        )
        self.queue = DFSPriQueueFSTrunc()

    cpdef void branch(TruncateBnB self, Node node):
        cdef:
            # int k
            DFSPriQueueFSTrunc queue
            list[Node] children
            Node child

        queue = <DFSPriQueueFSTrunc>self.queue
        queue.reset()

        children = node.branch()
        for child in children:
            self._node_eval(child)

        children.sort(key=_node_lb)
        # k = 0
        if children:
            for child in children:
                self._enqueue_core(child)
                # if k % 2 == 0:
                queue.next()
                # k += 1
        else:
            self.log_row('Cutoff')
        if not self.save_tree and node is not self.root:
            node.cleanup()
            del node


cpdef float _node_lb(Node node):
    return node.lb


cdef class CallbackBnBAge(CallbackBnB):

    def __init__(
        self,
        rtol=0.0001,
        atol=0.0001,
        eval_node='in',
        save_tree=False,
        restart_freq=RESTART,
    ):
        super().__init__(rtol, atol, eval_node, save_tree, restart_freq)
        self.sol_age = 0

    cpdef Node dequeue(CallbackBnBAge self):
        self.sol_age += 1
        if (self.sol_age % self.restart_freq) == 0:
            return self.queue.pop_lower_bound()
        return super(CallbackBnBAge, self).dequeue()
