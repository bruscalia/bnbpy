# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.string cimport string

import logging
from collections import defaultdict
from typing import List, Literal, Optional

from bnbprob.pfssp.cpp.environ cimport (
    JobPtr,
    Permutation,
    local_search,
    neh_constructive,
    quick_constructive,
    intensify
)
from bnbprob.pfssp.cython.solution cimport FlowSolution
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
        solution: FlowSolution,
        constructive: Literal['neh', 'quick'] = 'neh',
    ) -> None:
        self.solution = solution
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
            FlowSolution solution
        perm = Permutation(p)
        solution = FlowSolution()
        solution.perm = perm
        return cls(
            solution,
            constructive=constructive,
        )

    cpdef FlowSolution warmstart(PermFlowShop self):
        if self.constructive == 'neh':
            return self.neh_constructive()
        return self.quick_constructive()

    cpdef FlowSolution quick_constructive(PermFlowShop self):
        cdef:
            Permutation perm
            FlowSolution solution
            vector[JobPtr] jobs

        jobs = self.get_solution().perm.get_sequence_copy()
        perm = quick_constructive(jobs)
        solution = FlowSolution()
        solution.perm = perm
        return solution

    cpdef FlowSolution neh_constructive(PermFlowShop self):
        cdef:
            Permutation perm
            FlowSolution solution
            vector[JobPtr] jobs

        jobs = self.get_solution().perm.get_sequence_copy()
        perm = neh_constructive(jobs)
        solution = FlowSolution()
        solution.perm = perm
        return solution

    cpdef FlowSolution local_search(PermFlowShop self):
        cdef:
            double lb, new_cost
            Permutation perm
            FlowSolution sol_alt
            vector[JobPtr] jobs

        lb = self.solution.lb
        jobs = self.get_solution().perm.get_sequence_copy()
        perm = local_search(jobs)
        sol_alt = FlowSolution()
        sol_alt.perm = perm
        new_cost = perm.calc_lb_full()
        if new_cost < lb:
            sol_alt.set_feasible()
            sol_alt.set_lb(new_cost)
            return sol_alt
        return None

    cpdef FlowSolution intensification(PermFlowShop self):
        cdef:
            double new_cost, lb
            Permutation perm
            FlowSolution sol_alt, sol_ls
            vector[JobPtr] jobs

        perm = intensify(
            self.get_solution().perm
        )
        sol_alt = FlowSolution()
        sol_alt.perm = perm
        new_cost = perm.calc_lb_full()
        sol_alt.set_lb(new_cost)
        sol_alt.set_feasible()

        return sol_alt

    cpdef double calc_bound(PermFlowShop self):
        return self.get_solution().perm.calc_lb_1m()

    cpdef bool is_feasible(PermFlowShop self):
        return self.get_solution().perm.is_feasible()

    cpdef list[PermFlowShop] branch(PermFlowShop self):
        # Get fixed and unfixed job lists to create new solution
        cdef:
            int j, J
            list[PermFlowShop] out

        J = self.get_solution().perm.free_jobs.size()
        out = [None] * J
        for j in range(J):
            out[j] = self._child_push(j)
        return out

    cdef PermFlowShop _child_push(PermFlowShop self, int& j):
        cdef:
            PermFlowShop child = self._copy()

        child.get_solution().push_job(j)
        return child

    cpdef void bound_upgrade(PermFlowShop self):
        cdef:
            double lb5, lb
            FlowSolution current

        current = self.get_solution()
        if current.perm.free_jobs.size() == 0:
            lb5 = <double>current.perm.calc_lb_full()
        else:
            lb5 = <double>current.lower_bound_2m()

        lb = max(self.solution.lb, lb5)
        self.solution.set_lb(lb)

    cpdef int calc_idle_time(PermFlowShop self):
        return self.get_solution().perm.calc_idle_time()

    cpdef PermFlowShop copy(PermFlowShop self, bool deep=False):
        return self._copy()

    cdef PermFlowShop _copy(PermFlowShop self):
        cdef:
            PermFlowShop child
        child = type(self).__new__(type(self))
        child.solution = self.solution._copy()
        child.constructive = self.constructive
        return child


cdef class PermFlowShop1M(PermFlowShop):

    cpdef double calc_bound(PermFlowShop1M self):
        return self.get_solution().perm.calc_lb_1m()

    cpdef void bound_upgrade(PermFlowShop1M self):
        return


cdef class PermFlowShop2MHalf(PermFlowShop):

    cpdef void bound_upgrade(PermFlowShop2MHalf self):
        if self.get_solution().perm.level < (self.get_solution().perm.n // 2) + 1:
            return
        super(PermFlowShop2MHalf, self).bound_upgrade()


cdef class PermFlowShop2M(PermFlowShop):

    cpdef double calc_bound(PermFlowShop2M self):
        return self.get_solution().perm.calc_lb_2m()


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
            FlowSolution current

        current = self.get_solution()
        if current.perm.free_jobs.size() == 0:
            lb5 = <double>current.perm.calc_lb_full()
        else:
            lb5 = <double>current.lower_bound_2m()

        if lb5 >= self.solution.lb:
            self.lb_counter[current.perm.level, 'lb5'].pynext()
        else:
            self.lb_counter[current.perm.level, 'lb1'].pynext()

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
            FlowSolution current

        if not self.do_lb5:
            return
            # if self.get_solution().perm.level < (self.get_solution().perm.n // 2) + 1:
            #     return

        current = self.get_solution()
        if current.perm.free_jobs.size() == 0:
            lb5 = <double>current.perm.calc_lb_full()
        else:
            lb5 = <double>current.lower_bound_2m()

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
            FlowSolution current

        current = self.get_solution()
        if current.perm.free_jobs.size() == 0:
            lb5 = <double>current.perm.calc_lb_full()
        else:
            lb5 = <double>current.lower_bound_2m()

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
