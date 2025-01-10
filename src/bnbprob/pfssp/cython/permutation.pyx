# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.algorithm cimport sort
from libcpp.memory cimport make_shared, shared_ptr
from libcpp.vector cimport vector

from cython.operator cimport dereference as deref

from bnbprob.pfssp.cython.job cimport Job, JobPtr, PyJob, copy_job, start_job, fill_job, free_job
from bnbprob.pfssp.cython.sequence cimport (
    PySigma,
    Sigma,
    empty_sigma,
    job_to_bottom,
    job_to_top
)


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
        perm.free_jobs = vector[JobPtr](n)

        # Create jobs used in permutation solution
        perm.unsafe_alloc = True
        for j in range(n):
            # jobptr = start_job(j, p[j])
            pj = p[j]
            perm.free_jobs[j] = make_shared[Job]()
            fill_job(perm.free_jobs[j], j, pj)

        # Assign parameters
        perm.sigma1 = empty_sigma(m)
        perm.sigma2 = empty_sigma(m)
        perm.level = 0
        # perm._update_params()
        return perm

    def __del__(Permutation self):
        if self.unsafe_alloc:
            self._clean_jobs()

    cpdef void clean_jobs(Permutation self):
        self._clean_jobs()

    cdef void _clean_jobs(Permutation self):
        cdef:
            int j
            JobPtr job
            vector[JobPtr] seq

        seq = self.get_sequence()
        for j in range(seq.size()):
            free_job(seq[j])
            # del job

    cpdef list[PyJob] get_free_jobs(Permutation self):
        cdef:
            int i
            PyJob job
            JobPtr cjob
            list[PyJob] out

        out = []
        for i in range(self.free_jobs.size()):
            job = PyJob.__new__(PyJob)
            cjob = self.free_jobs[i]
            job.job = cjob
            out.append(job)
        return out

    cdef vector[JobPtr] _get_free_jobs(Permutation self):
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

    def get_indexes(self):
        cdef:
            int j
            vector[JobPtr] vec
            JobPtr job
        idx = []
        vec = self.get_sequence_copy()
        for j in range(vec.size()):
            idx.append(deref(vec[j]).j)
        return idx

    cdef vector[JobPtr] get_sequence(Permutation self):
        cdef:
            vector[JobPtr] seq
        seq = vector[JobPtr]()
        seq.insert(seq.end(), self.sigma1.jobs.begin(), self.sigma1.jobs.end())
        seq.insert(seq.end(), self.free_jobs.begin(), self.free_jobs.end())
        seq.insert(seq.end(), self.sigma2.jobs.begin(), self.sigma2.jobs.end())
        return seq

    cdef vector[JobPtr] get_sequence_copy(Permutation self):
        cdef:
            int j
            JobPtr job
            vector[JobPtr] base_seq
            vector[JobPtr] seq

        base_seq = self.get_sequence()
        seq = vector[JobPtr](base_seq.size())
        for j in range(base_seq.size()):
            seq[j] = copy_job(base_seq[j])
        return seq

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
                    job.r[k - 1] + job.p[k - 1]
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
                    job.q[m - k + 1] + job.p[m - k + 1]
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
            job.r[m] = job.r[m - 1] + job.p[m - 1]

        for j in range(1, seq.size()):
            job = &deref(seq[j])
            prev = &deref(seq[j - 1])
            job.r[0] = prev.r[0] + prev.p[0]
            for m in range(1, self.m):
                job.r[m] = max(
                    job.r[m - 1] + job.p[m - 1],
                    prev.r[m] + prev.p[m]
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
            Job* job

        max_value = 0

        for k in range(self.m):
            min_r = LARGE_INT
            min_q = LARGE_INT
            sum_p = 0

            for jobptr in self.free_jobs:
                job = &deref(jobptr)
                if job.r[k] < min_r:
                    min_r = job.r[k]
                if job.q[k] < min_q:
                    min_q = job.q[k]
                sum_p += job.p[k]

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
            Job* job

        r = vector[int](self.m, 0)
        for m in range(self.m):
            min_rm = LARGE_INT
            for jobptr in self.free_jobs:
                job = &deref(jobptr)
                if job.r[m] < min_rm:
                    min_rm = job.r[m]
            r[m] = min_rm

        return r

    cdef vector[int] get_q(Permutation self):
        cdef:
            int j, m, min_qm
            vector[int] q
            JobPtr jobptr
            Job* job

        q = vector[int](self.m, 0)
        for m in range(self.m):
            min_qm = LARGE_INT
            for jobptr in self.free_jobs:
                job = &deref(jobptr)
                if job.q[m] < min_qm:
                    min_qm = job.q[m]
            q[m] = min_qm

        return q

    cpdef Permutation copy(Permutation self):
        return self._copy()

    cdef Permutation _copy(Permutation self):
        cdef:
            int j
            Permutation perm
            Sigma s1, s2

        perm = Permutation.__new__(Permutation)
        perm.m = self.m
        perm.n = self.n
        perm.free_jobs = vector[JobPtr](self.free_jobs.size())
        for j in range(self.free_jobs.size()):
            perm.free_jobs[j] = copy_job(self.free_jobs[j])
        perm.sigma1 = self.sigma1
        perm.sigma2 = self.sigma2
        perm.level = self.level
        return perm


cdef inline bool desc_T(JobPtr a, JobPtr b):
    return deref(a).T > deref(b).T  # Sort by T in descending order


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


cdef int two_mach_problem(vector[JobPtr]& jobs, int m1, int m2):
    cdef:
        int J, j, t1, t2, res
        Job* job
        JobParams jparam
        vector[JobParams] j1, j2

    J = jobs.size()

    j1 = vector[JobParams]()
    j2 = vector[JobParams]()

    for j in range(J):
        job = &deref(jobs[j])
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
    vector[JobParams]& job_times,
    int m1,
    int m2
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
