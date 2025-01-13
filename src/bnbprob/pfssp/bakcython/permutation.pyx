# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.algorithm cimport sort
from libcpp.vector cimport vector

from array import array

from bnbprob.pfssp.cython.job cimport Job, start_job
from bnbprob.pfssp.cython.sequence cimport Sigma, empty_sigma


cdef:
    int LARGE_INT = 10000000


cdef Permutation create_permutation(
    int m,
    vector[Job] free_jobs,
    Sigma sigma1,
    Sigma sigma2,
    int level
):
    cdef:
        Permutation perm

    perm = Permutation.__new__(Permutation)
    perm.m = m
    perm.free_jobs = free_jobs
    perm.sigma1 = sigma1
    perm.sigma2 = sigma2
    perm.level = level
    perm.update_params()


cdef class Permutation:

    def __del__(self):
        self.cleanup()

    cdef void cleanup(Permutation self):
        self.free_jobs = None
        self.sigma1 = None
        self.sigma2 = None

    @staticmethod
    def from_p(p: list[list[int]]):
        cdef:
            int j, m
            list[int] pi
            Job job
            list[Job] jobs
            Sigma sigma1
            Sigma sigma2

        m = <int>len(p[0])
        jobs = [
            start_job(j, p[j])
            for j in range(len(p))
        ]

        return start_perm(m, jobs)

    @property
    def sequence(self) -> list[Job]:
        """Sequence of jobs in current solution"""
        return self.get_sequence()

    @property
    def n_jobs(self):
        return len(self.free_jobs) + len(self.sigma1.jobs) + len(self.sigma2.jobs)

    @property
    def n_free(self):
        return len(self.free_jobs)

    cpdef vector[Job] get_sequence(Permutation self):
        cdef:
            vector[Job] seq
        seq = vector[Job]()
        seq.insert(seq.end(), self.sigma1.jobs.begin(), self.self.sigma1.jobs.end())
        seq.insert(seq.end(), self.free_jobs.begin(), self.free_jobs.end())
        seq.insert(seq.end(), self.sigma2.jobs.begin(), self.self.sigma2.jobs.end())
        return seq

    cpdef vector[Job] get_sequence_copy(Permutation self):
        cdef:
            int i
            Job job
            vector[Job] seq

        seq = vector[Job]()
        for i in range(self.sigma1.jobs.size()):
            job = self.sigma1.jobs[i]
            seq.push_back(job)
        for i in range(self.free_jobs.size()):
            job = self.free_jobs[i]
            seq.push_back(job)
        for i in range(self.sigma2.jobs.size()):
            job = self.sigma2.jobs[i]
            seq.push_back(job)
        return seq

    cpdef int calc_bound(Permutation self):
        return self.calc_lb_2m()

    cpdef bool is_feasible(Permutation self):
        cdef:
            bool valid
        valid = <int>len(self.free_jobs) == 0
        if valid:
            self.compute_starts()
        return valid

    cpdef void push_job(Permutation self, int j):
        cdef:
            Job job
        job = self.free_jobs.pop(j)
        if self.level % 2 == 0:
            self.sigma1.job_to_bottom(job)
            self.front_updates()
        else:
            self.sigma2.job_to_top(job)
            self.back_updates()
        self.level += 1

    cpdef void update_params(Permutation self):
        self.front_updates()
        self.back_updates()

    cdef void front_updates(Permutation self):
        cdef:
            int k
            Job job

        for job in self.free_jobs:
            job.r[0] = self.sigma1.C[0]
            for k in range(1, self.m):
                job.r[k] = max(
                    self.sigma1.C[k],
                    job.r[k - 1] + job.p[k - 1]
                )

    cdef void back_updates(Permutation self):
        cdef:
            int k, m
            Job job

        m = self.m - 1
        for job in self.free_jobs:
            job.q[m] = self.sigma2.C[m]
            for k in range(1, m + 1):
                job.q[m - k] = max(
                    self.sigma2.C[m - k],
                    job.q[m - k + 1] + job.p[m - k + 1]
                )

    cpdef int calc_lb_1m(Permutation self):
        # All positions are filled take values from self
        if <int>len(self.free_jobs) == 0:
            return self.calc_lb_full()
        # Otherwise, use usual LB1
        return self.lower_bound_1m()

    cpdef int calc_lb_2m(Permutation self):
        cdef:
            int lb1, lb5
        # All positions are filled take values from self
        if <int>len(self.free_jobs) == 0:
            return self.calc_lb_full()
        # Use the greater between 1 and 2 machines
        lb1 = self.lower_bound_1m()
        lb5 = self.lower_bound_2m()
        return max(lb1, lb5)

    cpdef int calc_lb_full(Permutation self):
        cdef:
            int k, cost
        # All positions are filled take values from self
        cost = self.sigma1.C[0] + self.sigma2.C[0]
        for k in range(1, self.m):
            cost = max(cost, self.sigma1.C[k] + self.sigma2.C[k])
        return cost

    cpdef void compute_starts(Permutation self):
        cdef:
            int m, j
            Job job, prev
            list[Job] seq

        seq = self.get_sequence()
        for j in range(len(seq)):
            job = seq[j]
            job.r = vector[int](self.m, 0)

        job = seq[0]
        for m in range(1, self.m):
            job.r[m] = job.r[m - 1] + job.p[m - 1]

        for j in range(1, len(seq)):
            job = seq[j]
            prev = seq[j - 1]
            job.r[0] = prev.r[0] + prev.p[0]
            for m in range(1, self.m):
                job.r[m] = max(
                    job.r[m - 1] + job.p[m - 1],
                    prev.r[m] + prev.p[m]
                )

    cpdef int lower_bound_1m(Permutation self):
        cdef:
            int k, min_r, min_q, sum_p, max_value, temp_value
            Job job

        max_value = 0

        for k in range(self.m):
            min_r = LARGE_INT
            min_q = LARGE_INT
            sum_p = 0

            for job in self.free_jobs:
                if job.r[k] < min_r:
                    min_r = job.r[k]
                if job.q[k] < min_q:
                    min_q = job.q[k]
                sum_p += job.p[k]

            temp_value = min_r + sum_p + min_q
            if temp_value > max_value:
                max_value = temp_value

        return max_value

    cpdef int lower_bound_2m(Permutation self):
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

    cdef vector[int] get_r(Permutation self):
        cdef:
            int j, m, min_rm
            vector[int] r
            Job job

        r = vector[int](self.m, 0)
        for m in range(self.m):
            min_rm = LARGE_INT
            for job in self.free_jobs:
                if job.r[m] < min_rm:
                    min_rm = job.r[m]
            r[m] = min_rm

        return r

    cdef vector[int] get_q(Permutation self):
        cdef:
            int j, m, min_qm
            vector[int] q
            Job job

        q = vector[int](self.m, 0)
        for m in range(self.m):
            min_qm = LARGE_INT
            for job in self.free_jobs:
                if job.q[m] < min_qm:
                    min_qm = job.q[m]
            q[m] = min_qm

        return q

    cpdef Permutation copy(Permutation self):
        cdef:
            Job job
            Permutation perm

        perm = Permutation.__new__(Permutation)
        perm.m = self.m
        perm.free_jobs = [job.copy() for job in self.free_jobs]
        perm.sigma1 = self.sigma1.copy()
        perm.sigma2 = self.sigma2.copy()
        perm.level = self.level
        return perm


cdef Permutation start_perm(int m, list[Job] free_jobs):
    cdef:
        Permutation perm

    perm = Permutation.__new__(Permutation)
    perm.m = m
    perm.free_jobs = free_jobs
    perm.sigma1 = empty_sigma(m)
    perm.sigma2 = empty_sigma(m)
    perm.level = 0
    perm.update_params()
    return perm


cpdef inline int key_1_sort(tuple[Job, int, int] x):
    return x[1]


cpdef inline int key_2_sort(tuple[Job, int, int] x):
    return x[2]


cdef inline bool asc_t1(const JobParams& a, const JobParams& b):
    return a.t1 < b.t1  # Sort by t1 in ascending order


cdef inline bool desc_t2(const JobParams& a, const JobParams& b):
    return b.t2 < a.t2  # Sort by t2 in descending order


cdef int two_mach_problem(list[Job] jobs, int m1, int m2):
    cdef:
        int J, j, t1, t2, res
        Job job
        JobParams jparam
        vector[JobParams] j1, j2

    J = <int>len(jobs)

    j1 = vector[JobParams]()
    j2 = vector[JobParams]()

    for j in range(J):
        job = jobs[j]
        t1 = job.p[m1] + job.lat[m2][m1]
        t2 = job.p[m2] + job.lat[m2][m1]

        jparam = JobParams(t1, t2, &job.p[m1], &job.p[m2], &job.lat[m2][m1])

        if t1 <= t2:
            j1.push_back(jparam)
        else:
            j2.push_back(jparam)

    # Sort set1 in ascending order of t1
    sort(j1.begin(), j1.end(), asc_t1)

    # Sort set2 in descending order of t2
    sort(j2.begin(), j2.end(), desc_t2)

    # Include j2 into j1
    j1.insert(j1.end(), j2.begin(), j2.end())

    # Concatenate the sorted lists
    res = two_mach_makespan(j1, m1, m2)
    return res


cdef int two_mach_makespan(
    vector[JobParams] &job_times,
    int m1,
    int m2
):
    cdef:
        int j, time_m1, time_m2
        Job job

    time_m1 = 0  # Completion time for machine 1
    time_m2 = 0  # Completion time for machine 2

    for j in range(job_times.size()):
        # Machine 1 processes each job sequentially
        time_m1 += job_times[j].p1[0]

        # Machine 2 starts after the job is done
        # on Machine 1 and any lag is considered
        time_m2 = max(
            time_m1 + job_times[j].lat[0],
            time_m2
        ) + job_times[j].p2[0]

    return max(time_m1, time_m2)
