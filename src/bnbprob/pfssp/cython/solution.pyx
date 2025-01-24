# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector

from bnbprob.pfssp.cpp.environ cimport JobPtr, Permutation
from bnbprob.pfssp.cython.pyjob cimport PyJob, job_to_py
from bnbpy.cython.solution cimport Solution
from bnbpy.cython.status cimport OptStatus


cdef extern from "math.h":
    double HUGE_VAL


cdef class FlowSolution(Solution):

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

    cpdef bool is_feasible(FlowSolution self):
        return self.perm.is_feasible()

    cpdef int calc_lb_1m(FlowSolution self):
        return self.perm.calc_lb_1m()

    cpdef int calc_lb_2m(FlowSolution self):
        return self.perm.calc_lb_2m()

    cpdef int lower_bound_1m(FlowSolution self):
        return self.perm.lower_bound_1m()

    cpdef int lower_bound_2m(FlowSolution self):
        return self.perm.lower_bound_2m()

    cpdef void push_job(FlowSolution self, int& j):
        self.perm.push_job(j)

    cdef void _push_job(FlowSolution self, int& j):
        self.perm.push_job(j)

    cpdef FlowSolution copy(FlowSolution self, bool deep=False):
        return self._copy()

    cdef FlowSolution _copy(FlowSolution self):
        cdef:
            FlowSolution sol

        sol = FlowSolution.__new__(FlowSolution)
        sol.perm = self.perm.copy()
        sol.cost = HUGE_VAL
        sol.lb = 0
        sol._status = OptStatus.NO_SOLUTION
        return sol
