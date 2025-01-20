# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector

from bnbprob.pfssp.cpp.environ cimport JobPtr, Permutation
from bnbprob.pfssp.cython.pyjob cimport PyJob, job_to_py
from bnbpy.status import OptStatus


cdef:
    int LARGE_INT = 10000000


cdef class FlowSolution:

    def __init__(self):
        self.cost = LARGE_INT
        self.lb = 0
        self.status = OptStatus.NO_SOLUTION

    def __del__(self):
        pass

    def __repr__(self) -> str:
        return self._signature

    def __str__(self) -> str:
        return self._signature

    @property
    def _signature(self):
        return (
            f'Status: {self.status.name} | Cost: {self.cost} | LB: {self.lb}'
        )

    def get_status_cls(self):
        return self.status.__class__

    def get_status_options(self):
        status_cls = self.get_status_cls()
        return {status.name: status.value for status in status_cls}

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

    cpdef void set_optimal(FlowSolution self):
        self.status = OptStatus.OPTIMAL

    cpdef void set_lb(FlowSolution self, int lb):
        self.lb = lb
        if self.status == OptStatus.NO_SOLUTION:
            self.status = OptStatus.RELAXATION

    cpdef void set_feasible(FlowSolution self):
        self.status = OptStatus.FEASIBLE
        self.cost = self.lb

    cpdef void set_infeasible(FlowSolution self):
        self.status = OptStatus.INFEASIBLE
        self.cost = LARGE_INT

    cpdef void fathom(FlowSolution self):
        self.status = OptStatus.FATHOM
        self.cost = LARGE_INT

    cpdef bool is_feasible(FlowSolution self):
        return self.perm.is_feasible()

    cpdef int calc_lb_1m(FlowSolution self):
        return self.perm.calc_lb_1m()

    cpdef int calc_lb_2m(FlowSolution self):
        return self.perm.calc_lb_2m()

    cpdef int lower_bound_1m(FlowSolution self):
        return self.perm.lower_bound_1m()

    cpdef int lower_bound_2m(FlowSolution self):
        return self.perm.lower_bound_1m()

    cpdef void push_job(FlowSolution self, int& j):
        self.perm.push_job(j)

    cdef void _push_job(FlowSolution self, int& j):
        self.perm.push_job(j)

    cpdef FlowSolution copy(FlowSolution self):
        return self.copy()

    cdef FlowSolution _copy(FlowSolution self):
        cdef:
            FlowSolution sol

        sol = FlowSolution.__new__(FlowSolution)
        sol.perm = self.perm.copy()
        sol.cost = LARGE_INT
        sol.lb = 0
        sol.status = OptStatus.NO_SOLUTION
        return sol