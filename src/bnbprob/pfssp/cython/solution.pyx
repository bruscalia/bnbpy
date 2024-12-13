# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True

from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.algorithm cimport sort

from bnbprob.pfssp.cython.job cimport CyJob, copy_job, start_job
from bnbprob.pfssp.cython.sequence cimport Sigma, copy_sigma, job_to_bottom, job_to_top

import copy
from typing import Any, Optional, Union

from bnbpy.status import OptStatus


cdef:
    int LARGE_INT = 10000000


cdef class CyPermutation:
    # Not defined exactly as a Solution to be Cythonized

    def __init__(self):
        self.cost = LARGE_INT
        self.lb = 0
        self.status = OptStatus.NO_SOLUTION

    def __repr__(self) -> str:
        return self._signature

    def __str__(self) -> str:
        return self._signature

    @property
    def _signature(self):
        return (
            f'Status: {self.status.name} | Cost: {self.cost} | LB: {self.lb}'
        )

    def set_optimal(self):
        self.status = OptStatus.OPTIMAL

    def set_lb(self, lb: int):
        self.lb = lb
        if self.status == OptStatus.NO_SOLUTION:
            self.status = OptStatus.RELAXATION

    def set_feasible(self):
        self.status = OptStatus.FEASIBLE
        self.cost = self.lb

    def set_infeasible(self):
        self.status = OptStatus.INFEASIBLE
        self.cost = LARGE_INT

    def fathom(self):
        self.status = OptStatus.FATHOM
        self.cost = LARGE_INT

    @classmethod
    def from_p(cls, p: List[List[int]]):
        cdef:
            int j, m
            vector[int] pi
            CyJob job
            vector[CyJob] jobs
            Sigma sigma1
            Sigma sigma2
            CyPermutation perm

        m = len(p[0])
        jobs = vector[CyJob]()
        for j in range(len(p)):
            job = start_job(j, p[j])
            jobs.push_back(job)

        sigma1 = Sigma(vector[CyJob](), vector[int](m, 0))
        sigma2 = Sigma(vector[CyJob](), vector[int](m, 0))

        perm = cls()
        perm.assign(m, jobs, sigma1, sigma2, 0)
        return perm

    @property
    def sequence(self) -> List[Job]:
        """Sequence of jobs in current solution"""
        return self.get_sequence()

    @property
    def n_jobs(self):
        return len(self.sequence)

    @property
    def n_free(self):
        return <int>self.free_jobs.size()

    cpdef void assign(
        self,
        int m,
        vector[CyJob]& free_jobs,
        Sigma& sigma1,
        Sigma& sigma2,
        int level
    ):
        self.m = m
        self.free_jobs = free_jobs
        self.sigma1 = sigma1
        self.sigma2 = sigma2
        self.level = level

    cdef vector[CyJob] get_sequence(CyPermutation self):
        cdef:
            vector[CyJob] seq = vector[CyJob]()

        seq.insert(seq.end(), self.sigma1.jobs.begin(), self.sigma1.jobs.end())
        seq.insert(seq.end(), self.free_jobs.begin(), self.free_jobs.end())
        seq.insert(seq.end(), self.sigma2.jobs.begin(), self.sigma2.jobs.end())
        return seq

    cdef vector[CyJob] get_sequence_copy(CyPermutation self):
        cdef:
            int j
            CyJob job
            vector[CyJob] seq, seq_copy

        seq = self.get_sequence()
        seq_copy = vector[CyJob]()

        for j in range(seq.size()):
            job = seq[j]
            seq_copy.push_back(job.copy())

        return seq

    cpdef int calc_bound(CyPermutation self):
        return self.calc_lb_2m()

    cpdef bool is_feasible(CyPermutation self):
        cdef:
            bool valid
        valid = <int>self.free_jobs.size() == 0
        if valid:
            self.compute_starts()
        return valid

    cpdef void push_job(CyPermutation self, int& j):
        if self.level % 2 == 0:
            job_to_bottom(self.sigma1, self.free_jobs[j])
            self.free_jobs.erase(self.free_jobs.begin() + j)
            self.front_updates()
        else:
            job_to_top(self.sigma2, self.free_jobs[j])
            self.free_jobs.erase(self.free_jobs.begin() + j)
            self.back_updates()
        self.level += 1

    cpdef void update_params(CyPermutation self):
        self.front_updates()
        self.back_updates()

    cdef void front_updates(CyPermutation self):
        cdef:
            int j, k
        for j in range(self.free_jobs.size()):
            self.free_jobs[j].r[0] = self.sigma1.C[0]
            for k in range(1, self.m):
                self.free_jobs[j].r[k] = max(
                    self.sigma1.C[k],
                    self.free_jobs[j].r[k - 1] + self.free_jobs[j].p[k - 1]
                )

    cdef void back_updates(CyPermutation self):
        cdef:
            int j, k, m

        m = self.m - 1
        for j in range(self.free_jobs.size()):
            self.free_jobs[j].q[m] = self.sigma2.C[m]
            for k in range(1, m + 1):
                self.free_jobs[j].q[m - k] = max(
                    self.sigma2.C[m - k],
                    self.free_jobs[j].q[m - k + 1] + self.free_jobs[j].p[m - k + 1]
                )

    cpdef int calc_lb_1m(CyPermutation self):
        # All positions are filled take values from self
        if <int>self.free_jobs.size() == 0:
            return self.calc_lb_full()
        # Otherwise, use usual LB1
        return self.lower_bound_1m()

    cpdef int calc_lb_2m(CyPermutation self):
        """Computes lower bounds using 2M + 1M relaxations"""
        cdef:
            int lb1, lb5
        # All positions are filled take values from self
        if <int>self.free_jobs.size() == 0:
            return self.calc_lb_full()
        # Use the greater between 1 and 2 machines
        lb1 = self.lower_bound_1m()
        lb5 = self.lower_bound_2m()
        return max(lb1, lb5)

    cpdef int calc_lb_full(CyPermutation self):
        """Computes lower bounds for when there are no free jobs"""
        cdef:
            int k, cost
        # All positions are filled take values from self
        cost = self.sigma1.C[0] + self.sigma2.C[0]
        for k in range(self.m):
            cost = max(cost, self.sigma1.C[k] + self.sigma2.C[k])
        return cost

    cpdef void compute_starts(CyPermutation self):
        """
        Given a current sequence re-compute attributes release time `r`
        for each job on each machine
        """
        cdef:
            int m, j
            vector[CyJob] seq

        seq = self.get_sequence()
        for j in range(seq.size()):
            seq[j].r = vector[int](self.m, 0)

        seq[0].r[0] = 0
        for m in range(1, self.m):
            seq[0].r[m] = seq[0].r[m - 1] + seq[0].p[m - 1]

        for j in range(1, seq.size()):
            seq[j].r[0] = seq[j - 1].r[0] + seq[j - 1].p[0]
            for m in range(1, self.m):
                seq[j].r[m] = max(
                    seq[j].r[m - 1] + seq[j].p[m - 1],
                    seq[j - 1].r[m] + seq[j - 1].p[m]
                )

    cpdef int lower_bound_1m(CyPermutation self):
        cdef:
            int j, k, min_r, min_q, sum_p, max_value, temp_value

        max_value = 0

        for k in range(self.m):
            min_r = LARGE_INT
            min_q = LARGE_INT
            sum_p = 0

            for j in range(self.free_jobs.size()):
                if self.free_jobs[j].r[k] < min_r:
                    min_r = self.free_jobs[j].r[k]
                if self.free_jobs[j].q[k] < min_q:
                    min_q = self.free_jobs[j].q[k]
                sum_p += self.free_jobs[j].p[k]

            temp_value = min_r + sum_p + min_q
            if temp_value > max_value:
                max_value = temp_value

        return max_value

    cpdef int lower_bound_2m(CyPermutation self):
        cdef:
            int m1, m2, lbs, temp_value
            vector[int] r, q

        lbs = 0
        r = self.get_r()
        q = self.get_q()

        for m1 in range(self.m - 1):
            for m2 in range(m1 + 1, self.m):
                temp_value = (
                    r[m1]
                    + two_mach_problem(self.free_jobs, m1, m2)
                    + q[m2]
                )
                if temp_value > lbs:
                    lbs = temp_value

        return lbs

    cdef vector[int] get_r(self):
        cdef:
            int j, m, min_rm
            vector[int] r

        r = vector[int]()
        for m in range(self.m):
            min_rm = LARGE_INT
            for j in range(self.free_jobs.size()):
                if self.free_jobs[j].r[m] < min_rm:
                    min_rm = self.free_jobs[j].r[m]
            r.push_back(min_rm)

        return r

    cdef vector[int] get_q(self):
        cdef:
            int j, m, min_qm
            vector[int] r

        q = vector[int]()
        for m in range(self.m):
            min_qm = LARGE_INT
            for j in range(self.free_jobs.size()):
                if self.free_jobs[j].q[m] < min_qm:
                    min_qm = self.free_jobs[j].q[m]
            q.push_back(min_qm)

        return q

    cpdef CyPermutation quick_constructive(CyPermutation self):
        cdef:
            int i
            CyPermutation sol
        sol = self.copy()
        sort(sol.free_jobs.begin(), sol.free_jobs.end(), desc_slope)
        for i in range(sol.free_jobs.size()):
            job_to_bottom(sol.sigma1, sol.free_jobs[0])
            sol.free_jobs.erase(sol.free_jobs.begin())
        return sol

    cpdef CyPermutation neh_constructive(CyPermutation self):
        cdef:
            int c1, c2, j, i, k, best_cost, seq_size, cost_alt
            CyPermutation s1, s2, sol, s_alt
            CyJob job, job_i
            vector[CyJob] vec

        # Find best order of two jobs with longest processing times
        sort(self.free_jobs.begin(), self.free_jobs.end(), desc_T)

        vec = vector[CyJob](2)
        vec[0] = self.free_jobs[0]
        vec[1] = self.free_jobs[1]
        s1 = CyPermutation()
        s1.assign(
            self.m,
            vec,
            self.sigma1,
            self.sigma2,
            self.level
        )

        vec = vector[CyJob](2)
        vec[0] = self.free_jobs[1]
        vec[1] = self.free_jobs[0]
        s2 = CyPermutation()
        s2.assign(
            self.m,
            vec,
            self.sigma1,
            self.sigma2,
            self.level
        )

        c1 = s1.calc_bound()
        c2 = s2.calc_bound()
        if c1 <= c2:
            sol = s1
        else:
            sol = s2

        # Find best insert for every other job
        seq_size = 2
        for j in range(2, self.free_jobs.size()):
            best_cost = LARGE_INT
            best_sol = self
            # Positions in sequence
            for i in range(seq_size + 1):
                s_alt = CyPermutation()
                s_alt.assign(
                    sol.m,
                    sol.get_sequence(),
                    Sigma(vector[CyJob](), vector[int](sol.m, 0)),
                    Sigma(vector[CyJob](), vector[int](sol.m, 0)),
                    0
                )
                job = self.free_jobs[j]
                s_alt.free_jobs.insert(s_alt.free_jobs.begin() + i, job)
                # Fix all jobs
                for k in range(s_alt.free_jobs.size()):
                    job_to_bottom(s_alt.sigma1, s_alt.free_jobs[0])
                    s_alt.free_jobs.erase(s_alt.free_jobs.begin())
                cost_alt = s_alt.calc_bound()
                # Update best of iteration
                if cost_alt < best_cost:
                    best_cost = cost_alt
                    best_sol = s_alt
            seq_size += 1
            sol = best_sol
        return sol

    cpdef CyPermutation local_search(CyPermutation self):
        cdef:
            int i, j, k, best_cost, new_cost
            CyPermutation sol_base, best_move
            CyJob job

        # A new base solution following the same sequence of the current
        sol_base = CyPermutation()
        sol_base.assign(
            self.m,
            self.get_sequence_copy(),
            Sigma(vector[CyJob](), vector[int](self.m, 0)),
            Sigma(vector[CyJob](), vector[int](self.m, 0)),
            0
        )

        # The release date in the first machine must be recomputed
        # As positions might change
        recompute_r0(sol_base.free_jobs)
        best_move = CyPermutation()
        best_move.assign(
            self.m,
            self.get_sequence_copy(),
            Sigma(vector[CyJob](), vector[int](self.m, 0)),
            Sigma(vector[CyJob](), vector[int](self.m, 0)),
            0
        )
        for i in range(best_move.free_jobs.size()):
            job_to_bottom(best_move.sigma1, best_move.free_jobs[0])
            best_move.free_jobs.erase(best_move.free_jobs.begin())
        best_cost = best_move.calc_bound()

        # Try to remove every job
        for i in range(sol_base.free_jobs.size()):
            # The current list decreases size in one unit after removal
            for j in range(sol_base.free_jobs.size()):
                # Job shouldn't be inserted in the same original position
                # and avoids symmetric swaps
                if j == i or j == i + 1:
                    continue

                # Here the swap is performed
                sol_alt = sol_base.copy()
                job = sol_alt.free_jobs[i]
                sol_alt.free_jobs.erase(sol_alt.free_jobs.begin() + i)
                sol_alt.free_jobs.insert(sol_alt.free_jobs.begin() + j, job)

                # In the new solution jobs are sequentially
                # inserted in the last position, so only sigma 1 is modified
                # Updates to sigma C for each machine are automatic
                for k in range(sol_alt.free_jobs.size()):
                    job_to_bottom(sol_alt.sigma1, sol_alt.free_jobs[0])
                    sol_alt.free_jobs.erase(sol_alt.free_jobs.begin())

                # New bound is computed considering sigma C
                new_cost = sol_alt.calc_bound()
                if new_cost < best_cost:
                    best_move = sol_alt
                    best_cost = new_cost

        return best_move

    cpdef CyPermutation copy(CyPermutation self):
        cdef:
            int j
            CyPermutation other
            vector[CyJob] new_jobs

        new_jobs = vector[CyJob]()
        for j in range(self.free_jobs.size()):
            new_jobs.push_back(copy_job(self.free_jobs[j]))

        other = CyPermutation()
        other.assign(
            self.m,
            new_jobs,
            copy_sigma(self.sigma1),
            copy_sigma(self.sigma2),
            self.level,
        )
        return other


# cdef class Permutation:
#     perm: CyPermutation

#     cost: Optional[Union[int, float]]
#     lb: Union[int, float]
#     status: OptStatus

#     def __init__(self, lb=LOW_NEG):
#         self.cost = None
#         self.lb = lb
#         self.status = OptStatus.NO_SOLUTION

#     def __repr__(self) -> str:
#         return self._signature

#     def __str__(self) -> str:
#         return self._signature

#     @property
#     def _signature(self):
#         return (
#             f'Status: {self.status.name} | Cost: {self.cost} | LB: {self.lb}'
#         )

#     def set_optimal(self):
#         self.status = OptStatus.OPTIMAL

#     def set_lb(self, lb: int):
#         self.lb = lb
#         if self.status == OptStatus.NO_SOLUTION:
#             self.status = OptStatus.RELAXATION

#     def set_feasible(self):
#         self.status = OptStatus.FEASIBLE
#         self.cost = self.lb

#     def set_infeasible(self):
#         self.status = OptStatus.INFEASIBLE
#         self.cost = None

#     def fathom(self):
#         self.status = OptStatus.FATHOM
#         self.cost = None

#     def __init__(
#         self,
#         perm: CyPermutation,
#     ):
#         super().__init__()
#         self.perm = perm

    # @classmethod
    # def from_p(cls, p: List[List[int]]):
    #     cdef:
    #         int j, m
    #         vector[int] pi
    #         CyJob job
    #         vector[CyJob] jobs
    #         Sigma sigma1
    #         Sigma sigma2
    #         CyPermutation perm

    #     m = len(p[0])
    #     jobs = vector[CyJob]()
    #     for j in range(len(p)):
    #         job = start_job(j, p[j])
    #         jobs.push_back(job)

    #     sigma1 = Sigma(vector[CyJob](), vector[int](m, 0))
    #     sigma2 = Sigma(vector[CyJob](), vector[int](m, 0))

    #     perm = CyPermutation()
    #     perm.assign(m, jobs, sigma1, sigma2, 0)
    #     return cls(perm)

    # @property
    # def sequence(self) -> List[Job]:
    #     """Sequence of jobs in current solution"""
    #     return self.perm.get_sequence()

    # @property
    # def n_jobs(self):
    #     return len(self.sequence)

    # @property
    # def n_free(self):
    #     return len(self.perm.free_jobs)

    # def calc_bound(self):
    #     return self.perm.calc_lb_2m()

    # def is_feasible(self) -> bool:
    #     return self.perm.is_feasible()

    # def push_job(self, j: int):
    #     return self.perm.push_job(j)

    # def update_params(self):
    #     return self.perm.update_params()

    # def calc_lb_1m(self) -> Optional[int]:
    #     """Computes lower bounds using 1M relaxation"""
    #     return self.perm.calc_lb_1m()

    # def calc_lb_2m(self) -> Optional[int]:
    #     """Computes lower bounds using 2M + 1M relaxations"""
    #     # All positions are filled take values from self
    #     return self.perm.calc_lb_2m()

    # def calc_lb_full(self) -> Optional[int]:
    #     """Computes lower bounds for when there are no free jobs"""
    #     # All positions are filled take values from self
    #     return self.perm.calc_lb_full()

    # def compute_starts(self):
    #     """
    #     Given a current sequence re-compute attributes release time `r`
    #     for each job on each machine
    #     """
    #     return self.perm.compute_starts()

    # def lower_bound_1m(self):
    #     return self.perm.lower_bound_1m()

    # def lower_bound_2m(self):
    #     return self.perm.lower_bound_2m()

    # def quick_constructive(self):
    #     return Permutation(self.perm.quick_constructive())

    # def neh_constructive(self):
    #     return Permutation(self.perm.neh_constructive())

    # def local_search(self):
    #     return Permutation(self.perm.local_search())

    # def copy(self, deep=False):
    #     if deep:
    #         return copy.deepcopy(self)
    #     other = Permutation(
    #         self.perm.copy()
    #     )
    #     return other


cdef class PyPermutation:

    cdef public:
        CyPermutation perm

    def __init__(self, p: List[List[int]], level: int = 0):
        cdef:
            int j, m
            vector[int] pi
            CyJob job
            vector[CyJob] jobs
            Sigma sigma1
            Sigma sigma2

        m = len(p[0])
        jobs = vector[CyJob]()
        for j in range(len(p)):
            job = start_job(j, p[j])
            jobs.push_back(job)

        sigma1 = Sigma(vector[CyJob](), vector[int](m, 0))
        sigma2 = Sigma(vector[CyJob](), vector[int](m, 0))

        self.perm = CyPermutation()
        self.perm.assign(m, jobs, sigma1, sigma2, level)

    def get_sequence(self):
        return list(self.perm.get_sequence())

    def calc_bound(self) -> int:
        return self.perm.calc_lb_2m()

    def is_feasible(self) -> bool:
        return self.perm.is_feasible()

    def push_job(self, j: int):
        return self.perm.push_job(j)

    def calc_lb_1m(self) -> int:
        return self.perm.calc_lb_1m()

    def calc_lb_2m(self) -> int:
        return self.perm.calc_lb_2m()

    def calc_lb_full(self) -> int:
        return self.perm.calc_lb_full()

    def compute_starts(self) -> None:
        return self.perm.compute_starts()

    def lower_bound_1m(self) -> int:
        return self.perm.lower_bound_1m()

    def lower_bound_2m(self) -> int:
        return self.perm.lower_bound_2m()


cdef void recompute_r0(vector[CyJob]& jobs):
    cdef:
        int j
    jobs[0].r[0] = 0
    for j in range(1, jobs.size()):
        jobs[j].r[0] = jobs[j - 1].r[0] + jobs[j - 1].p[0]


cdef int two_mach_problem(vector[CyJob]& jobs, int& m1, int& m2):
    cdef:
        int J, j, t1, t2, res
        TwoMachParam jparam
        vector[TwoMachParam] job_times, j1, j2, opt

    J = <int>jobs.size()

    job_times = vector[TwoMachParam]()
    j1 = vector[TwoMachParam]()
    j2 = vector[TwoMachParam]()

    for j in range(J):
        t1 = jobs[j].p[m1] + jobs[j].lat[m2][m1]
        t2 = jobs[j].p[m2] + jobs[j].lat[m2][m1]

        jparam = TwoMachParam(&jobs[j], t1, t2)

        if t1 <= t2:
            j1.push_back(jparam)
        else:
            j2.push_back(jparam)

    # Sort set1 in ascending order of t1
    sort(j1.begin(), j1.end(), asc_t1)

    # Sort set2 in descending order of t2
    sort(j2.begin(), j2.end(), desc_t2)

    # Concatenate the sorted lists
    job_times.reserve(j1.size() + j2.size())  # Optimize memory allocation
    job_times.insert(job_times.end(), j1.begin(), j1.end())
    job_times.insert(job_times.end(), j2.begin(), j2.end())

    res = two_mach_makespan(job_times, m1, m2)
    return res


cdef int two_mach_makespan(
    vector[TwoMachParam]& job_times,
    int& m1,
    int& m2
):
    cdef:
        int j, time_m1, time_m2

    time_m1 = 0  # Completion time for machine 1
    time_m2 = 0  # Completion time for machine 2

    for j in range(job_times.size()):
        # Machine 1 processes each job sequentially
        time_m1 += job_times[j].job.p[m1]

        # Machine 2 starts after the job is done
        # on Machine 1 and any lag is considered
        time_m2 = max(
            time_m1 + job_times[j].job.lat[m2][m1],
            time_m2
        ) + job_times[j].job.p[m2]

    return max(time_m1, time_m2)
