# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool

from bnbprob.pfssp.cython.job cimport Job
from bnbprob.pfssp.cython.permutation cimport Permutation, start_perm

cdef:
    int LARGE_INT = 10000000


cpdef Permutation quick_constructive(list[Job] jobs):
    cdef:
        int i, M
        Permutation sol
        Job job

    M = <int>len(jobs[0].p)
    sol = start_perm(M, jobs)
    sol.free_jobs.sort(key=key_slope_sort, reverse=True)
    for i in range(len(sol.free_jobs)):
        job = sol.free_jobs.pop(0)
        sol.sigma1.job_to_bottom(job)
    return sol


cpdef Permutation neh_constructive(list[Job] jobs):
    cdef:
        int c1, c2, j, i, k, M, best_cost, seq_size, cost_alt
        Permutation s1, s2, sol, s_alt
        Job job, job_i
        list[Job] vec

    # Find best order of two jobs with longest processing times
    jobs.sort(key=key_T_sort, reverse=True)

    M = <int>len(jobs[0].p)

    vec = [jobs[0].pycopy(), jobs[1].pycopy()]
    s1 = start_perm(M, vec)
    for k in range(len(s1.free_jobs)):
        job_i = s1.free_jobs.pop(0)
        s1.sigma1.job_to_bottom(job_i)

    vec = [jobs[1].pycopy(), jobs[0].pycopy()]
    s2 = start_perm(M, vec)
    for k in range(len(s2.free_jobs)):
        job_i = s2.free_jobs.pop(0)
        s2.sigma1.job_to_bottom(job_i)

    c1 = s1.calc_bound()
    c2 = s2.calc_bound()
    if c1 <= c2:
        sol = s1
    else:
        sol = s2

    # Find best insert for every other job
    seq_size = 2
    for j in range(2, len(jobs)):
        best_cost = LARGE_INT
        best_sol = start_perm(M, [])
        # Positions in sequence
        for i in range(seq_size + 1):
            s_alt = start_perm(sol.m, sol.get_sequence_copy())
            job = jobs[j]
            s_alt.free_jobs.insert(i, job.copy())
            # Fix all jobs
            for k in range(len(s_alt.free_jobs)):
                job_i = s_alt.free_jobs.pop(0)
                s_alt.sigma1.job_to_bottom(job_i)
            cost_alt = s_alt.calc_bound()
            # Update best of iteration
            if cost_alt < best_cost:
                best_cost = cost_alt
                best_sol = s_alt
        seq_size += 1
        sol = best_sol
    return sol


cpdef Permutation local_search(Permutation perm):
    cdef:
        bool solved
        int i, j, k, best_cost, new_cost
        Permutation sol_base, best_move
        Job job

    # Solved will only be updated in case a good solution is found
    solved = False

    # A new base solution following the same sequence of the current
    sol_base = start_perm(perm.m, perm.get_sequence_copy())

    # The release date in the first machine must be recomputed
    # As positions might change
    recompute_r0(sol_base.free_jobs)
    best_move = start_perm(perm.m, perm.get_sequence_copy())
    for i in range(len(best_move.free_jobs)):
        job = best_move.free_jobs.pop(0)
        best_move.sigma1.job_to_bottom(job)
    best_cost = best_move.calc_bound()

    # Try to remove every job
    for i in range(len(sol_base.free_jobs)):
        # The current list decreases size in one unit after removal
        for j in range(len(sol_base.free_jobs)):
            # Job shouldn't be inserted in the same original position
            # and avoids symmetric swaps
            if j == i or j == i + 1:
                continue

            # Here the swap is performed
            sol_alt = sol_base.copy()
            job = sol_alt.free_jobs.pop(i)
            sol_alt.free_jobs.insert(j, job)
            # Careful recomputation althuogh it worked without it
            # probably because of memoryviews
            recompute_r0(sol_alt.free_jobs)

            # In the new solution jobs are sequentially
            # inserted in the last position, so only sigma 1 is modified
            # Updates to sigma C for each machine are automatic
            for k in range(len(sol_alt.free_jobs)):
                job = sol_alt.free_jobs.pop(0)
                sol_alt.sigma1.job_to_bottom(job)

            # New bound is computed considering sigma C
            new_cost = sol_alt.calc_bound()
            if new_cost < best_cost:
                best_move = sol_alt
                best_cost = new_cost
                solved = True

    return best_move


cpdef inline int key_T_sort(Job x):
    return x.get_T()


cpdef inline int key_slope_sort(Job x):
    return x.get_slope()


cdef void recompute_r0(list[Job] jobs):
    cdef:
        int j
    jobs[0].r[0] = 0
    for j in range(1, len(jobs)):
        jobs[j].r[0] = jobs[j - 1].r[0] + jobs[j - 1].p[0]
