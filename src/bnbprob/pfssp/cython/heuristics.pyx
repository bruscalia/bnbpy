# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.algorithm cimport sort
from libcpp.vector cimport vector

from cython.operator cimport dereference as deref

from bnbprob.pfssp.cython.job cimport JobPtr
from bnbprob.pfssp.cython.permutation cimport Permutation, start_perm
from bnbprob.pfssp.cython.sequence cimport Sigma, empty_sigma, job_to_bottom

cdef:
    int LARGE_INT = 10000000


cdef Permutation quick_constructive(vector[JobPtr]& jobs) except *:
    cdef:
        int i, M
        Permutation sol

    M = <int>jobs.size()
    sort(jobs.begin(), jobs.end(), desc_slope)
    sol = start_perm(M, jobs)
    for i in range(sol.free_jobs.size()):
        job_to_bottom(sol.sigma1, sol.free_jobs[0])
        sol.free_jobs.erase(sol.free_jobs.begin())
        sol.front_updates()
    return sol


cdef Permutation neh_constructive(vector[JobPtr]& jobs) except *:
    cdef:
        int c1, c2, j, i, k, M, best_cost, seq_size, cost_alt
        Permutation s1, s2, sol, best_sol, s_alt
        JobPtr job, job_i
        vector[JobPtr] vec

    # Find best order of two jobs with longest processing times
    sort(jobs.begin(), jobs.end(), desc_T)

    M = <int>deref(jobs[0]).r.size()

    vec = vector[JobPtr](2)
    vec[0] = jobs[0]
    vec[1] = jobs[1]
    s1 = start_perm(M, vec)
    for k in range(s1.free_jobs.size()):
        job_to_bottom(s1.sigma1, s1.free_jobs[0])
        s1.free_jobs.erase(s1.free_jobs.begin())

    vec = vector[JobPtr](2)
    vec[0] = jobs[1]
    vec[1] = jobs[0]
    s2 = start_perm(M, vec)
    for k in range(s2.free_jobs.size()):
        job_to_bottom(s2.sigma1, s2.free_jobs[0])
        s2.free_jobs.erase(s2.free_jobs.begin())

    c1 = s1.calc_lb_full()
    c2 = s2.calc_lb_full()
    if c1 <= c2:
        sol = s1
    else:
        sol = s2

    # Find best insert for every other job
    seq_size = 2
    for j in range(seq_size, jobs.size()):
        best_cost = LARGE_INT
        best_sol = Permutation.__new__(Permutation)
        # Positions in sequence
        for i in range(seq_size + 1):
            job = jobs[j]
            vec = sol.get_sequence_copy()
            vec.insert(vec.begin() + i, job)
            s_alt = start_perm(M, vec)
            # Fix all jobs
            for k in range(s_alt.free_jobs.size()):
                job_to_bottom(s_alt.sigma1, s_alt.free_jobs.at(0))
                s_alt.free_jobs.erase(s_alt.free_jobs.begin())
            cost_alt = s_alt.calc_lb_full()
            # Update best of iteration
            if cost_alt < best_cost:
                best_cost = cost_alt
                best_sol = s_alt
        seq_size += 1
        sol = best_sol
    return sol


cpdef Permutation local_search(Permutation perm) except *:
    cdef:
        bool solved
        int i, j, k, best_cost, new_cost
        Permutation sol_base, best_move
        JobPtr job
        vector[JobPtr] vec

    # Solved will only be updated in case a good solution is found
    solved = False

    # A new base solution following the same sequence of the current
    vec = perm.get_sequence_copy()
    sol_base = start_perm(perm.m, vec)

    # The release date in the first machine must be recomputed
    # As positions might change
    recompute_r0(sol_base.free_jobs)
    best_move = start_perm(perm.m, perm.get_sequence_copy())
    for i in range(best_move.free_jobs.size()):
        job_to_bottom(best_move.sigma1, best_move.free_jobs.at(0))
        best_move.free_jobs.erase(best_move.free_jobs.begin())
    best_cost = best_move.calc_lb_full()

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
            # Careful recomputation althuogh it worked without it
            # probably because of memoryviews
            recompute_r0(sol_alt.free_jobs)

            # In the new solution jobs are sequentially
            # inserted in the last position, so only sigma 1 is modified
            # Updates to sigma C for each machine are automatic
            for k in range(sol_alt.free_jobs.size()):
                job_to_bottom(sol_alt.sigma1, sol_alt.free_jobs.at(0))
                sol_alt.free_jobs.erase(sol_alt.free_jobs.begin())

            # New bound is computed considering sigma C
            new_cost = sol_alt.calc_lb_full()
            if new_cost < best_cost:
                best_move = sol_alt
                best_cost = new_cost
                solved = True

    return best_move


cdef inline bool desc_T(JobPtr& a, JobPtr& b):
    return deref(b).T < deref(a).T  # Sort by T in descending order


cdef inline bool desc_slope(JobPtr& a, JobPtr& b):
    return deref(b).slope < deref(a).slope  # Sort by slope in descending order


cdef void recompute_r0(vector[JobPtr]& jobs):
    cdef:
        int j
    deref(jobs[0]).r[0] = 0
    for j in range(1, jobs.size()):
        deref(jobs[j]).r[0] = deref(jobs[j - 1]).r[0] + deref(jobs[j - 1]).p[0]
