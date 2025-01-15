# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.algorithm cimport sort
from libcpp.memory cimport make_shared, shared_ptr
from libcpp.vector cimport vector

from cython.operator cimport dereference as deref

from bnbprob.pfssp.cython.job cimport Job, JobPtr, copy_jobs
from bnbprob.pfssp.cython.sequence cimport (
    PySigma,
    Sigma,
    empty_sigma,
    job_to_bottom,
    job_to_top
)
from bnbprob.pfssp.cython.pyjob cimport PyJob


cdef:
    int LARGE_INT = 10000000


cdef class Permutation:

    @staticmethod
    def from_p(p: list[list[int]]):
        cdef:
            int j, m, n
            JobPtr jobptr
            vector[JobPtr] jobs
            vector[int] pj
            Sigma sigma1
            Sigma sigma2
            Permutation perm

        m = <int>len(p[0])
        n = <int>len(p)

        # Instantiate the permutation
        perm = Permutation.__new__(Permutation)
        perm.m = m
        perm.n = n
        perm.free_jobs = vector[JobPtr]()

        # Create jobs used in permutation solution
        for j in range(n):
            pj = p[j]
            perm.free_jobs.push_back(
                make_shared[Job](j, pj)
            )

        # Assign parameters
        perm.sigma1 = empty_sigma(m)
        perm.sigma2 = empty_sigma(m)
        perm.level = 0
        perm._update_params()
        return perm

    cdef vector[JobPtr] get_free_jobs(Permutation self):
        return self.free_jobs

    cpdef PySigma get_sigma1(Permutation self):
        cdef:
            int i
            PySigma out

        out = PySigma.__new__(PySigma)
        out.sigma = self.sigma1
        return out

    cdef Sigma _get_sigma1(Permutation self):
        return self.sigma1

    cpdef PySigma get_sigma2(Permutation self):
        cdef:
            int i
            PySigma out

        out = PySigma.__new__(PySigma)
        out.sigma = self.sigma2
        return out

    cdef Sigma _get_sigma2(Permutation self):
        return self.sigma2

    cdef vector[JobPtr] get_sequence(Permutation self):
        cdef:
            vector[JobPtr] seq
        seq = vector[JobPtr]()
        seq.insert(seq.end(), self.sigma1.jobs.begin(), self.sigma1.jobs.end())
        seq.insert(seq.end(), self.free_jobs.begin(), self.free_jobs.end())
        seq.insert(seq.end(), self.sigma2.jobs.begin(), self.sigma2.jobs.end())
        return seq

    cdef inline vector[JobPtr] get_sequence_copy(Permutation self):
        return copy_jobs(self.get_sequence())

    cdef bool is_feasible(Permutation self):
        cdef:
            bool valid
        valid = self.free_jobs.size() == 0
        if valid:
            self.compute_starts()
        return valid

    cdef void _push_job(Permutation self, int j):
        if self.level % 2 == 0:
            job_to_bottom(self.sigma1, self.free_jobs[j])
            self.free_jobs.erase(self.free_jobs.begin() + j)
            self.front_updates()
        else:
            job_to_top(self.sigma2, self.free_jobs[j])
            self.free_jobs.erase(self.free_jobs.begin() + j)
            self.back_updates()
        self.level += 1

    cpdef void push_job(Permutation self, int j):
        self._push_job(j)

    cpdef void update_params(Permutation self):
        self.front_updates()
        self.back_updates()

    cdef void _update_params(Permutation self):
        self.front_updates()
        self.back_updates()

    cdef void front_updates(Permutation self):
        cdef:
            JobPtr jobptr
            Job* job
            int k, j

        for j in range(self.free_jobs.size()):
            job = &deref(self.free_jobs[j])
            job.r[0] = self.sigma1.C[0]
            for k in range(1, self.m):
                job.r[k] = max(
                    self.sigma1.C[k],
                    job.r[k - 1] + deref(job.p)[k - 1]
                )

    cdef void back_updates(Permutation self):
        cdef:
            int j, k, m
            JobPtr jobptr
            Job* job

        m = self.m - 1
        for j in range(self.free_jobs.size()):
            job = &deref(self.free_jobs[j])
            job.q[m] = self.sigma2.C[m]
            for k in range(1, m + 1):
                job.q[m - k] = max(
                    self.sigma2.C[m - k],
                    job.q[m - k + 1] + deref(job.p)[m - k + 1]
                )

    cpdef void compute_starts(Permutation self):
        self._compute_starts()

    cdef void _compute_starts(Permutation self):
        cdef:
            int m, j
            Job* job
            Job* prev
            vector[JobPtr] seq

        seq = self.get_sequence()
        for j in range(seq.size()):
            job = &deref(seq[j])
            job.r = vector[int](self.m, 0)

        job = &deref(seq[0])
        for m in range(1, self.m):
            job.r[m] = job.r[m - 1] + deref(job.p)[m - 1]

        for j in range(1, seq.size()):
            job = &deref(seq[j])
            prev = &deref(seq[j - 1])
            job.r[0] = prev.r[0] + deref(prev.p)[0]
            for m in range(1, self.m):
                job.r[m] = max(
                    job.r[m - 1] + deref(job.p)[m - 1],
                    prev.r[m] + deref(prev.p)[m]
                )

    cpdef int calc_lb_1m(Permutation self):
        # All positions are filled take values from self
        if self.free_jobs.size() == 0:
            return self._calc_lb_full()
        # Otherwise, use usual LB1
        return self.lower_bound_1m()

    cpdef int calc_lb_2m(Permutation self):
        cdef:
            int lb1, lb5
        # All positions are filled take values from self
        if self.free_jobs.size() == 0:
            return self._calc_lb_full()
        # Use the greater between 1 and 2 machines
        lb1 = self.lower_bound_1m()
        lb5 = self.lower_bound_2m()
        return max(lb1, lb5)

    cpdef int calc_lb_full(Permutation self):
        return self._calc_lb_full()

    cdef int _calc_lb_full(Permutation self):
        cdef:
            int k, cost
        # All positions are filled take values from self
        cost = self.sigma1.C[0] + self.sigma2.C[0]
        for k in range(1, self.m):
            cost = max(cost, self.sigma1.C[k] + self.sigma2.C[k])
        return cost

    cdef int lower_bound_1m(Permutation self):
        cdef:
            int k, min_r, min_q, sum_p, max_value, temp_value
            JobPtr jobptr

        max_value = 0

        for k in range(self.m):
            min_r = LARGE_INT
            min_q = LARGE_INT
            sum_p = 0

            for jobptr in self.free_jobs:
                if deref(jobptr).r[k] < min_r:
                    min_r = deref(jobptr).r[k]
                if deref(jobptr).q[k] < min_q:
                    min_q = deref(jobptr).q[k]
                sum_p += deref(deref(jobptr).p)[k]

            temp_value = min_r + sum_p + min_q
            if temp_value > max_value:
                max_value = temp_value

        return max_value

    cdef int lower_bound_2m(Permutation self):
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
            JobPtr jobptr

        r = vector[int](self.m, 0)
        for m in range(self.m):
            min_rm = LARGE_INT
            for jobptr in self.free_jobs:
                if deref(jobptr).r[m] < min_rm:
                    min_rm = deref(jobptr).r[m]
            r[m] = min_rm

        return r

    cdef vector[int] get_q(Permutation self):
        cdef:
            int j, m, min_qm
            vector[int] q
            JobPtr jobptr

        q = vector[int](self.m, 0)
        for m in range(self.m):
            min_qm = LARGE_INT
            for jobptr in self.free_jobs:
                if deref(jobptr).q[m] < min_qm:
                    min_qm = deref(jobptr).q[m]
            q[m] = min_qm

        return q

    cpdef Permutation copy(Permutation self):
        return self._copy()

    cpdef Permutation scopy(Permutation self):
        cdef:
            int j
            Permutation perm
            Sigma s1, s2

        perm = Permutation.__new__(Permutation)
        perm.m = self.m
        perm.n = self.n
        perm.free_jobs = self.free_jobs
        perm.sigma1 = self.sigma1
        perm.sigma2 = self.sigma2
        perm.level = self.level
        return perm

    cdef Permutation _copy(Permutation self):
        cdef:
            int j
            Permutation perm
            Sigma s1, s2

        perm = Permutation.__new__(Permutation)
        perm.m = self.m
        perm.n = self.n
        perm.free_jobs = copy_jobs(self.free_jobs)
        perm.sigma1 = self.sigma1
        perm.sigma2 = self.sigma2
        perm.level = self.level
        return perm


cdef Permutation start_perm(int m, vector[JobPtr]& jobs):
    cdef:
        int j
        Permutation perm

    perm = Permutation.__new__(Permutation)
    perm.m = m
    perm.n = <int> jobs.size()
    perm.free_jobs = jobs
    perm.sigma1 = empty_sigma(m)
    perm.sigma2 = empty_sigma(m)
    perm.level = 0
    perm._update_params()
    return perm


cdef inline bool asc_t1(const JobParams& a, const JobParams& b):
    return a.t1 < b.t1  # Sort by t1 in ascending order


cdef inline bool desc_t2(const JobParams& a, const JobParams& b):
    return b.t2 < a.t2  # Sort by t2 in descending order


cdef int two_mach_problem(vector[JobPtr]& jobs, int& m1, int& m2):
    cdef:
        int J, j, t1, t2, res
        Job* job
        vector[JobParams] j1, j2

    J = jobs.size()

    j1 = vector[JobParams]()
    j2 = vector[JobParams]()

    for j in range(J):
        job = &deref(jobs[j])
        t1 = deref(job.p)[m1] + deref(job.lat)[m2][m1]
        t2 = deref(job.p)[m2] + deref(job.lat)[m2][m1]

        if t1 <= t2:
            j1.push_back(
                JobParams(t1, t2, &deref(job.p)[m1], &deref(job.p)[m2], &deref(job.lat)[m2][m1])
            )
        else:
            j2.push_back(
                JobParams(t1, t2, &deref(job.p)[m1], &deref(job.p)[m2], &deref(job.lat)[m2][m1])
            )

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
    vector[JobParams]& job_times,
    int& m1,
    int& m2
):
    cdef:
        int j, time_m1, time_m2

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
