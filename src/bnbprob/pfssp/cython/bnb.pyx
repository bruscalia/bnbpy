# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from bnbprob.pfssp.cython.problem cimport PermFlowShop
from bnbprob.pfssp.cython.solution cimport FlowSolution
from bnbpy.cython.node cimport Node
from bnbpy.cython.search cimport BranchAndBound

cdef:
    int RESTART = 10_000


cdef class LazyBnB(BranchAndBound):

    def __init__(
        self, rtol=0.0001, atol=0.0001, eval_node='in', save_tree=False
    ):
        super(LazyBnB, self).__init__(rtol, atol, eval_node, save_tree)

    cpdef void post_eval_callback(LazyBnB self, Node node):
        cdef:
            PermFlowShop problem
        if node.lb < self.get_ub():
            problem = node.problem
            problem.bound_upgrade()
            node.lb = node.problem.get_lb()


cdef class CallbackBnB(LazyBnB):

    def __init__(
        self,
        rtol=0.0001,
        atol=0.0001,
        eval_node='in',
        save_tree=False,
        restart_freq=RESTART,
    ):
        super(CallbackBnB, self).__init__(rtol, atol, eval_node, save_tree)
        self.restart_freq = restart_freq

    cpdef void solution_callback(CallbackBnB self, Node node):
        cdef:
            PermFlowShop problem
            FlowSolution new_sol

        problem = node.problem
        new_sol = problem.local_search()
        if new_sol is not None:
            # General procedure in case is valid
            if new_sol.is_feasible() and new_sol.lb < node.get_solution().lb:
                node.set_solution(new_sol)
                node.check_feasible()
                self.set_solution(node)

    cpdef Node dequeue(CallbackBnB self):
        if self.explored % self.restart_freq == 0:
            return _min_queue(self.queue)
        return super(CallbackBnB, self).dequeue()


cdef Node _min_queue(list[tuple[object, Node]] queue):
    cdef:
        int i, N
        tuple[object, Node] x, min_x
        Node node, out

    N = len(queue)
    if N == 0:
        return None

    min_x = queue[0]
    node = min_x[1]
    out = node
    i = 1
    while i < N:
        x = queue[i]
        node = x[1]
        if node.lb < out.lb:
            min_x = x
            out = node
        i += 1
    queue.remove(min_x)
    return out



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
            return _min_queue(self.queue)
        return super(CallbackBnBAge, self).dequeue()
