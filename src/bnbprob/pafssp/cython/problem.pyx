# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.string cimport string
from libcpp.memory cimport shared_ptr

import logging
from typing import List, Literal, Optional, Tuple

from bnbprob.pafssp.cpp.environ cimport (
    JobPtr,
    MachineGraph,
    Permutation,
    intensify,
    intensify_ref,
    local_search,
    neh_constructive,
    quick_constructive,
    randomized_heur
)
from bnbprob.pafssp.cython.pyjob cimport PyJob, job_to_py
from bnbprob.pafssp.cython.pysigma cimport PySigma, sigma_to_py
from bnbprob.pafssp.cython.utils cimport create_machine_graph, get_mach_graph
from bnbprob.pafssp.machinegraph import MachineGraph as MachGraphInterface
from bnbpy.cython.problem cimport Problem
from bnbpy.cython.solution cimport Solution


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
        edges: Optional[List[Tuple[int, int]]] = None,
        constructive: Literal['neh', 'quick'] = 'neh'
    ) -> 'PermFlowShop':
        cdef:
            Permutation perm
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
        perm = Permutation(pp, mach_graph)

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
            return self.neh_constructive()
        return self.quick_constructive()

    cpdef PermFlowShop quick_constructive(PermFlowShop self):
        cdef:
            PermFlowShop child
            Permutation perm
            vector[JobPtr] jobs

        jobs = self.perm.get_sequence_copy()
        perm = quick_constructive(jobs, self.perm.mach_graph)
        child = self.fast_copy()
        child.perm = perm
        return child

    cpdef PermFlowShop neh_constructive(PermFlowShop self):
        cdef:
            PermFlowShop child
            Permutation perm
            vector[JobPtr] jobs

        jobs = self.perm.get_sequence_copy()
        perm = neh_constructive(jobs, self.perm.mach_graph)
        child = self.fast_copy()
        child.perm = perm
        return child

    cpdef PermFlowShop local_search(PermFlowShop self):
        cdef:
            double lb, new_cost
            Permutation perm
            PermFlowShop sol_alt
            vector[JobPtr] jobs

        lb = self.solution.lb
        jobs = self.perm.get_sequence_copy()
        perm = local_search(jobs, self.perm.mach_graph)
        new_cost = perm.calc_lb_full()
        if new_cost < lb:
            sol_alt = self.fast_copy()
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

        jobs = self.perm.get_sequence_copy()
        perm = randomized_heur(jobs, n_iter, seed, self.perm.mach_graph)
        sol_alt = self.fast_copy()
        sol_alt.perm = perm
        sol_alt.solution.set_feasible()
        sol_alt.solution.set_lb(perm.calc_lb_full())
        return sol_alt

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
