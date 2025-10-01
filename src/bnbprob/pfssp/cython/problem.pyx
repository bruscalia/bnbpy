# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.string cimport string

import logging
from collections import defaultdict
from typing import List, Literal

from bnbprob.pfssp.cpp.environ cimport (
    JobPtr,
    Permutation,
    ils,
    intensify,
    intensify_ref,
    local_search,
    neh_constructive,
    path_relinking,
    quick_constructive,
    randomized_heur
)
from bnbprob.pfssp.cython.pyjob cimport PyJob, job_to_py
from bnbpy.cython.counter cimport Counter
from bnbpy.cython.problem cimport Problem
from bnbpy.cython.solution cimport Solution
from bnbpy.cython.status cimport OptStatus

log = logging.getLogger(__name__)

cdef:
    Counter lb5_counter, lb1_counter

lb5_counter = Counter()
lb1_counter = Counter()


cpdef tuple[int, int] get_counts():
    return lb5_counter.get_value(), lb1_counter.get_value()


cdef class PermFlowShop(Problem):

    def __init__(
        self,
        constructive: Literal['neh', 'quick'] = 'neh',
    ) -> None:
        self.solution = Solution()
        self.constructive = <string> constructive.encode("utf-8")

    def __del__(self):
        self.ccleanup()

    cdef void ccleanup(PermFlowShop self):
        self.solution = None

    @classmethod
    def from_p(
        cls,
        p: List[List[int]],
        constructive: Literal['neh', 'quick'] = 'neh'
    ) -> 'PermFlowShop':
        cdef:
            Permutation perm
            PermFlowShop problem
        perm = Permutation(p)
        problem = cls(
            constructive=constructive,
        )
        problem.set_perm(perm)
        return problem

    @property
    def sequence(self):
        cdef:
            int i
            vector[JobPtr] seq
            PyJob job
        out = []
        seq = self.perm.get_sequence()
        for i in range(seq.size()):
            job = job_to_py(seq[i])
            out.append(job)
        return out

    @property
    def free_jobs(self):
        cdef:
            int i
            vector[JobPtr] seq
            PyJob job
        out = []
        seq = self.perm.get_free_jobs()[0]
        for i in range(seq.size()):
            job = job_to_py(seq[i])
            out.append(job)
        return out

    cpdef PermFlowShop warmstart(PermFlowShop self):
        if self.constructive == 'neh':
            return self.neh_constructive()
        return self.quick_constructive()

    cpdef PermFlowShop quick_constructive(PermFlowShop self):
        cdef:
            PermFlowShop child
            Permutation perm
            vector[JobPtr] jobs

        jobs = self.perm.get_sequence_copy()
        perm = quick_constructive(jobs)
        child = self.fast_copy()
        child.perm = perm
        return child

    cpdef PermFlowShop neh_constructive(PermFlowShop self):
        cdef:
            PermFlowShop child
            Permutation perm
            vector[JobPtr] jobs

        jobs = self.perm.get_sequence_copy()
        perm = neh_constructive(jobs)
        child = self.fast_copy()
        child.perm = perm
        return child

    cpdef PermFlowShop ils(
        PermFlowShop self,
        int max_iter=1000,
        int max_age=1000,
        int d=5,
        unsigned int seed=0
    ):
        cdef:
            PermFlowShop child
            vector[JobPtr] jobs

        jobs = self.perm.get_sequence_copy()
        child = self.fast_copy()
        child.perm = ils(jobs, max_iter, d, max_age, seed)
        return child

    cpdef PermFlowShop randomized_heur(
        PermFlowShop self,
        int n_iter=10,
        unsigned int seed=0
    ):
        cdef:
            PermFlowShop child
            vector[JobPtr] jobs

        jobs = self.perm.get_sequence_copy()
        child = self.fast_copy()
        child.perm = randomized_heur(jobs, n_iter, seed)
        return child

    cpdef PermFlowShop local_search(PermFlowShop self):
        cdef:
            double lb, new_cost
            Permutation perm
            PermFlowShop sol_alt
            vector[JobPtr] jobs

        lb = self.solution.lb
        jobs = self.perm.get_sequence_copy()
        perm = local_search(jobs)
        new_cost = perm.calc_lb_full()
        if new_cost < lb:
            sol_alt = self.fast_copy()
            sol_alt.perm = perm
            sol_alt.solution.set_feasible()
            sol_alt.solution.set_lb(new_cost)
            return sol_alt
        return None

    cpdef PermFlowShop intensification(PermFlowShop self):
        cdef:
            double new_cost, lb
            PermFlowShop sol_alt
            vector[JobPtr] jobs

        sol_alt = self.fast_copy()
        sol_alt.perm = intensify(self.perm)
        new_cost = sol_alt.perm.calc_lb_full()
        sol_alt.solution.set_lb(new_cost)
        sol_alt.solution.set_feasible()

        return sol_alt

    cpdef PermFlowShop intensification_ref(
        PermFlowShop self,
        PermFlowShop reference
    ):
        cdef:
            double new_cost, lb
            PermFlowShop sol_alt
            vector[JobPtr] jobs

        sol_alt = self.fast_copy()
        sol_alt.perm = intensify_ref(
            self.perm,
            reference.perm
        )
        new_cost = sol_alt.perm.calc_lb_full()
        sol_alt.solution.set_lb(new_cost)
        sol_alt.solution.set_feasible()

        return sol_alt

    cpdef PermFlowShop path_relinking(
        PermFlowShop self,
        PermFlowShop reference
    ):
        cdef:
            double new_cost, lb
            PermFlowShop sol_alt

        sol_alt = self.fast_copy()
        sol_alt.perm = intensify(
            path_relinking(
                self.perm,
                reference.perm
            )
        )
        new_cost = sol_alt.perm.calc_lb_full()
        print(f"Current cost: {self.perm.calc_lb_full()}")
        print(f"Path relinking cost: {new_cost}")
        sol_alt.solution.set_lb(new_cost)
        sol_alt.solution.set_feasible()

        return sol_alt

    cpdef double calc_bound(PermFlowShop self):
        return self.perm.calc_lb_1m()

    cpdef bool is_feasible(PermFlowShop self):
        return self.perm.is_feasible()

    cpdef list[PermFlowShop] branch(PermFlowShop self):
        # Get fixed and unfixed job lists to create new solution
        cdef:
            int j, J
            list[PermFlowShop] out

        J = self.perm.free_jobs.size()
        out = [None] * J
        for j in range(J):
            out[j] = self._child_push(j)
        return out

    cdef PermFlowShop _child_push(PermFlowShop self, int& j):
        cdef:
            PermFlowShop child = self._copy()

        child._push_job(j)
        return child

    cpdef void bound_upgrade(PermFlowShop self):
        cdef:
            double lb5, lb

        if self.perm.free_jobs.size() == 0:
            lb5 = <double>self.perm.calc_lb_full()
        else:
            lb5 = <double>self.lower_bound_2m()

        lb = max(self.solution.lb, lb5)
        self.solution.set_lb(lb)

    cpdef int calc_lb_1m(PermFlowShop self):
        return self.perm.calc_lb_1m()

    cpdef int calc_lb_2m(PermFlowShop self):
        return self.perm.calc_lb_2m()

    cpdef int lower_bound_1m(PermFlowShop self):
        return self.perm.lower_bound_1m()

    cpdef int lower_bound_2m(PermFlowShop self):
        return self.perm.lower_bound_2m()

    cpdef void push_job(PermFlowShop self, int& j):
        self.perm.push_job(j)

    cdef void _push_job(PermFlowShop self, int& j):
        self.perm.push_job(j)

    cpdef void compute_starts(PermFlowShop self):
        self.perm.compute_starts()

    cpdef int calc_idle_time(PermFlowShop self):
        return self.perm.calc_idle_time()

    cpdef int calc_tot_time(PermFlowShop self):
        return self.calc_tot_time()

    cpdef PermFlowShop copy(PermFlowShop self, bool deep=False):
        return self._copy()

    cdef PermFlowShop _copy(PermFlowShop self):
        cdef:
            PermFlowShop child
        child = type(self).__new__(type(self))
        child.solution = Solution()
        child.constructive = self.constructive
        child.perm = self.perm.copy()
        return child


cdef class PermFlowShop1M(PermFlowShop):

    cpdef double calc_bound(PermFlowShop1M self):
        return self.perm.calc_lb_1m()

    cpdef void bound_upgrade(PermFlowShop1M self):
        return


cdef class PermFlowShop2MHalf(PermFlowShop):

    cpdef void bound_upgrade(PermFlowShop2MHalf self):
        if self.perm.level < (self.perm.n // 3) + 1:
            return
        super(PermFlowShop2MHalf, self).bound_upgrade()


cdef class PermFlowShop2M(PermFlowShop):

    cpdef double calc_bound(PermFlowShop2M self):
        return self.perm.calc_lb_2m()


cdef class PermFlowShopLevelCount(PermFlowShop):

    def __init__(
        self,
        solution: FlowSolution,
        constructive: Literal['neh', 'quick'] = 'neh',
    ) -> None:
        super().__init__(solution, constructive)
        self.lb_counter = defaultdict(Counter)

    cpdef void bound_upgrade(PermFlowShopLevelCount self):
        cdef:
            double lb5, lb

        if self.perm.free_jobs.size() == 0:
            lb5 = <double>self.perm.calc_lb_full()
        else:
            lb5 = <double>self.lower_bound_2m()

        if lb5 >= self.solution.lb:
            self.lb_counter[self.perm.level, 'lb5'].pynext()
        else:
            self.lb_counter[self.perm.level, 'lb1'].pynext()

        lb = max(self.solution.lb, lb5)
        self.solution.set_lb(lb)

    cpdef PermFlowShopLevelCount copy(PermFlowShopLevelCount self, bool deep=False):
        return self._copy()

    cdef PermFlowShopLevelCount _copy(PermFlowShopLevelCount self):
        cdef:
            PermFlowShopLevelCount child
        child = type(self).__new__(type(self))
        child.solution = self.solution._copy()
        child.constructive = self.constructive
        child.lb_counter = self.lb_counter
        return child


cdef class PermFlowShopQuit(PermFlowShop):

    def __init__(
        self,
        solution: FlowSolution,
        constructive: Literal['neh', 'quick'] = 'neh',
    ) -> None:
        super().__init__(solution, constructive)
        self.do_lb5 = True

    cpdef void bound_upgrade(PermFlowShopQuit self):
        cdef:
            double lb5, lb

        if not self.do_lb5:
            return

        if self.perm.free_jobs.size() == 0:
            lb5 = <double>self.perm.calc_lb_full()
        else:
            lb5 = <double>self.lower_bound_2m()

        if lb5 < self.solution.lb:
            self.do_lb5 = False

        lb = max(self.solution.lb, lb5)
        self.solution.set_lb(lb)

    cpdef PermFlowShopQuit copy(PermFlowShopQuit self, bool deep=False):
        return self._copy()

    cdef PermFlowShopQuit _copy(PermFlowShopQuit self):
        cdef:
            PermFlowShopQuit child
        child = type(self).__new__(type(self))
        child.solution = self.solution._copy()
        child.constructive = self.constructive
        child.do_lb5 = self.do_lb5
        return child


cdef class UpgradeCounter:

    def __init__(self):
        self.stay_two_mach = Counter()
        self.switch_to_single = Counter()
        self.stay_single = Counter()
        self.switch_to_two_mach = Counter()

    def to_dict(self):
        return {
            'stay_two_mach': self.stay_two_mach.get_value(),
            'switch_to_single': self.switch_to_single.get_value(),
            'stay_single': self.stay_single.get_value(),
            'switch_to_two_mach': self.switch_to_two_mach.get_value(),
        }


cdef class PermFlowShopCounter(PermFlowShopQuit):

    def __init__(
        self,
        solution: FlowSolution,
        constructive: Literal['neh', 'quick'] = 'neh',
    ) -> None:
        super().__init__(solution, constructive)
        self.upgrade_counter = UpgradeCounter()

    cpdef void bound_upgrade(PermFlowShopCounter self):
        cdef:
            double lb5, lb

        if self.perm.free_jobs.size() == 0:
            lb5 = <double>self.perm.calc_lb_full()
        else:
            lb5 = <double>self.lower_bound_2m()

        # Here the lb5 outperformed, so either
        # stay or switch to two machines
        if lb5 >= self.solution.lb:
            if self.do_lb5:
                self.upgrade_counter.stay_two_mach.next()
            else:
                self.upgrade_counter.switch_to_two_mach.next()
            self.do_lb5 = True

        # Here the lb5 did not outperform, so either
        # stay or switch to single machine
        else:
            if self.do_lb5:
                self.upgrade_counter.switch_to_single.next()
            else:
                self.upgrade_counter.stay_single.next()
            self.do_lb5 = False
        lb = max(self.solution.lb, lb5)
        self.solution.set_lb(lb)

    cpdef PermFlowShopCounter copy(PermFlowShopCounter self, bool deep=False):
        return self._copy()

    cdef PermFlowShopCounter _copy(PermFlowShopCounter self):
        cdef:
            PermFlowShopCounter child
        child = type(self).__new__(type(self))
        child.solution = self.solution._copy()
        child.constructive = self.constructive
        child.do_lb5 = self.do_lb5
        child.upgrade_counter = self.upgrade_counter
        return child
