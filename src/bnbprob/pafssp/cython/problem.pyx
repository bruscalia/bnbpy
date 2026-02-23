# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.string cimport string
from cython.operator cimport dereference as deref

import logging
from typing import List, Literal, Optional, Tuple

from bnbprob.pafssp.cpp.environ cimport (
    JobPtr,
    MachineGraph,
    Permutation,
    iga,
    intensify,
    local_search,
    neh_initialization,
    quick_constructive,
    randomized_heur
)
from bnbprob.pafssp.cython.pyjob cimport PyJob, job_to_py
from bnbprob.pafssp.cython.pysigma cimport PySigma, sigma_to_py
from bnbprob.pafssp.cython.utils cimport create_machine_graph, get_mach_graph
from bnbprob.pafssp.machinegraph import MachineGraph as MachGraphInterface
from bnbpy.cython.problem cimport Problem
from bnbpy.cython.solution cimport Solution


cdef:
    int DEFAULT_SEED = 42


cdef class PermFlowShop(Problem):

    def __init__(
        self,
        constructive: Literal['neh', 'quick', 'multistart'] = 'neh',
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
        edges: Optional[List[Tuple[int, int]]] = None,
        constructive: Literal['neh', 'quick', 'multistart', 'iga'] = 'neh'
    ) -> 'PermFlowShop':
        cdef:
            PermFlowShop problem
            MachineGraph mach_graph
            vector[vector[int]] pp
            int m

        # Get number of machines from processing times
        m = len(p[0]) if p and p[0] else 0

        # Create sequential MachineGraph
        if edges is None:
            edges = [
                (i, i + 1) for i in range(m - 1)
            ]
        mi = MachGraphInterface.from_edges(edges)
        mach_graph = create_machine_graph(mi)

        # Create Permutation with processing times and MachineGraph
        pp = p

        problem = cls(
            constructive=constructive,
        )
        problem.set_perm(pp, mach_graph)
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
        seq = self.perm.get_free_jobs()
        for i in range(seq.size()):
            job = job_to_py(seq[i])
            out.append(job)
        return out

    @property
    def sigma1(self):
        cdef:
            PySigma py_sigma
        py_sigma = sigma_to_py(self.perm.sigma1)
        return py_sigma

    @property
    def sigma2(self):
        cdef:
            PySigma py_sigma
        py_sigma = sigma_to_py(self.perm.sigma2)
        return py_sigma

    cpdef object get_mach_graph(PermFlowShop self):
        cdef:
            MachineGraph mg_cpp
            object mg
        mg_cpp = self.perm.get_mach_graph()
        mg = get_mach_graph(mg_cpp)
        return mg

    cpdef PermFlowShop warmstart(PermFlowShop self):
        if self.constructive == 'neh':
            return self.neh_initialization()
        elif self.constructive == 'multistart':
            return self.multistart_initialization()
        elif self.constructive == 'iga':
            return self.iga_initialization()
        return self.quick_constructive()

    cpdef PermFlowShop quick_constructive(PermFlowShop self):
        cdef:
            PermFlowShop child
            Permutation perm
            vector[JobPtr] jobs

        jobs = self.perm.get_sequence()
        perm = quick_constructive(jobs, self.perm.mach_graph)
        child = self._copy()
        child.perm = perm
        return child

    cpdef PermFlowShop neh_initialization(PermFlowShop self):
        cdef:
            PermFlowShop child
            Permutation perm
            vector[JobPtr] jobs

        jobs = self.perm.get_sequence()
        perm = neh_initialization(jobs, self.perm.mach_graph)
        child = self._copy()
        child.perm = perm
        return child

    cpdef PermFlowShop multistart_initialization(PermFlowShop self):
        cdef:
            int n_iter, n_jobs, n_machines
            PermFlowShop child
            Permutation perm
            vector[JobPtr] jobs

        jobs = self.perm.get_sequence()
        n_jobs = jobs.size()
        if n_jobs > 0:
            n_machines = deref(jobs[0]).p.size()
            n_iter = n_jobs * n_machines
        else:
            n_iter = 0
        perm = randomized_heur(jobs, n_iter, DEFAULT_SEED, self.perm.mach_graph)
        child = self._copy()
        child.perm = perm
        return child

    cpdef PermFlowShop iga_initialization(PermFlowShop self):
        cdef:
            int n_jobs, n_iter, d
            Permutation perm
            PermFlowShop sol_alt, neh_sol
            vector[JobPtr] jobs

        neh_sol = self.neh_initialization()
        jobs = neh_sol.perm.get_sequence()
        n_jobs = jobs.size()
        if n_jobs > 0:
            n_machines = deref(jobs[0]).p.size()
            n_iter = n_jobs * n_machines
        else:
            n_iter = 0
        d = max(5, n_jobs // 10)
        perm = iga(jobs, self.perm.mach_graph, n_iter, d, DEFAULT_SEED)
        sol_alt = self._copy()
        sol_alt.perm = perm
        sol_alt.solution.set_feasible()
        sol_alt.solution.set_lb(perm.calc_lb_full())
        return sol_alt

    cpdef PermFlowShop local_search(PermFlowShop self):
        cdef:
            double lb, new_cost
            Permutation perm
            PermFlowShop sol_alt
            vector[JobPtr] jobs

        lb = self.solution.lb
        jobs = self.perm.get_sequence()
        perm = local_search(jobs, self.perm.mach_graph)
        new_cost = perm.calc_lb_full()
        if new_cost < lb:
            sol_alt = self._copy()
            sol_alt.perm = perm
            sol_alt.solution.set_feasible()
            sol_alt.solution.set_lb(new_cost)
            return sol_alt
        return None

    cpdef PermFlowShop randomized_heur(PermFlowShop self, int n_iter, unsigned int seed=0):
        cdef:
            Permutation perm
            PermFlowShop sol_alt
            vector[JobPtr] jobs

        jobs = self.perm.get_sequence()
        perm = randomized_heur(jobs, n_iter, seed, self.perm.mach_graph)
        sol_alt = self._copy()
        sol_alt.perm = perm
        sol_alt.solution.set_feasible()
        sol_alt.solution.set_lb(perm.calc_lb_full())
        return sol_alt

    cpdef PermFlowShop iga_heur(PermFlowShop self, int n_iter, int d, unsigned int seed=0):
        cdef:
            Permutation perm
            PermFlowShop sol_alt
            vector[JobPtr] jobs

        jobs = self.neh_initialization().perm.get_sequence()
        perm = iga(jobs, self.perm.mach_graph, n_iter, d, seed)
        sol_alt = self._copy()
        sol_alt.perm = perm
        sol_alt.solution.set_feasible()
        sol_alt.solution.set_lb(perm.calc_lb_full())
        return sol_alt

    cpdef PermFlowShop intensify(
        PermFlowShop self,
        PermFlowShop reference
    ):
        cdef:
            double new_cost, lb
            PermFlowShop sol_alt

        sol_alt = self._copy()
        sol_alt.perm = intensify(
            self.perm,
            reference.perm
        )
        new_cost = sol_alt.perm.calc_lb_full()
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

    cpdef void simple_bound_upgrade(PermFlowShop self):
        cdef:
            double lb

        if self.perm.free_jobs.size() == 0:
            lb = <double>self.perm.calc_lb_full()
        else:
            self.perm.update_params()
            lb = <double>self.lower_bound_1m()
        self.solution.set_lb(lb)

    cpdef void double_bound_upgrade(PermFlowShop self):
        self._double_bound_upgrade()

    cdef void _double_bound_upgrade(PermFlowShop self):
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

    cpdef void update_params(PermFlowShop self):
        self.perm.update_params()

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
        child = PermFlowShop.__new__(PermFlowShop)
        child.solution = Solution()
        child.constructive = self.constructive
        child.perm = self.perm
        return child

    cpdef void perm_copy(PermFlowShop self):
        cdef:
            Permutation perm
        perm = self.perm


cdef class BenchPermFlowShop(PermFlowShop):

    cpdef double calc_bound(BenchPermFlowShop self):
        self.perm.update_params()
        return self.perm.calc_lb_1m()

    cdef BenchPermFlowShop _copy(BenchPermFlowShop self):
        cdef:
            BenchPermFlowShop child
        child = BenchPermFlowShop.__new__(BenchPermFlowShop)
        child.solution = Solution()
        child.constructive = self.constructive
        child.perm = self.perm
        return child


cdef class PermFlowShop1M(PermFlowShop):

    cpdef double calc_bound(PermFlowShop1M self):
        return self.perm.calc_lb_1m()

    cpdef void double_bound_upgrade(PermFlowShop1M self):
        return

    cdef PermFlowShop1M _copy(PermFlowShop1M self):
        cdef:
            PermFlowShop1M child
        child = PermFlowShop1M.__new__(PermFlowShop1M)
        child.solution = Solution()
        child.constructive = self.constructive
        child.perm = self.perm
        return child
