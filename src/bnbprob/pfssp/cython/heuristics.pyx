# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool

import numpy as np

from bnbprob.pfssp.cython.job cimport Job, start_job
from bnbprob.pfssp.cython.sequence cimport Sigma
from bnbprob.pfssp.cython.permutation cimport Permutation

cdef:
    int LARGE_INT = 10000000


cpdef Permutation quick_constructive(Permutation perm):
    cdef:
        int i
        Permutation sol
        Job job

    sol = perm.copy()
    sol.free_jobs.sort(key=key_slope_sort, reverse=True)
    for i in range(len(sol.free_jobs)):
        job = sol.free_jobs.pop(0)
        sol.sigma1.job_to_bottom(job)
    return sol


cpdef Permutation neh_constructive(Permutation perm):
    cdef:
        int c1, c2, j, i, k, best_cost, seq_size, cost_alt
        int[:] C_empty
        Permutation s1, s2, sol, s_alt
        Job job, job_i
        list[Job] vec

    # Find best order of two jobs with longest processing times
    perm.free_jobs.sort(key=key_T_sort, reverse=True)

    vec = [perm.free_jobs[0], perm.free_jobs[1]]
    s1 = Permutation(
        perm.m,
        vec,
        perm.sigma1.copy(),
        perm.sigma2.copy(),
        perm.level
    )

    vec = [perm.free_jobs[1], perm.free_jobs[0]]
    s2 = Permutation(
        perm.m,
        vec,
        perm.sigma1.copy(),
        perm.sigma2.copy(),
        perm.level
    )

    c1 = s1.calc_bound()
    c2 = s2.calc_bound()
    if c1 <= c2:
        sol = s1
    else:
        sol = s2

    # Creates first C-empty instance
    C_empty = np.zeros(sol.m, dtype='i')[:]

    # Find best insert for every other job
    seq_size = 2
    for j in range(2, len(perm.free_jobs)):
        best_cost = LARGE_INT
        best_sol = perm.copy()
        # Positions in sequence
        for i in range(seq_size + 1):
            s_alt = Permutation(
                sol.m,
                sol.get_sequence_copy(),
                Sigma([], C_empty.copy()),
                Sigma([], C_empty.copy()),
                0
            )
            job = perm.free_jobs[j].copy()
            s_alt.free_jobs.insert(i, job)
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
        int[:] C_empty
        Permutation sol_base, best_move
        Job job

    # Solved will only be updated in case a good solution is found
    solved = False

    # Creates first C-empty instance
    C_empty = np.zeros(perm.m, dtype='i')[:]

    # A new base solution following the same sequence of the current
    sol_base = Permutation(
        perm.m,
        perm.get_sequence_copy(),
        Sigma([], C_empty.copy()),
        Sigma([], C_empty.copy()),
        0
    )

    # The release date in the first machine must be recomputed
    # As positions might change
    recompute_r0(sol_base.free_jobs)
    best_move = Permutation(
        perm.m,
        perm.get_sequence_copy(),
        Sigma([], C_empty.copy()),
        Sigma([], C_empty.copy()),
        0
    )
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
    return x.T


cpdef inline int key_slope_sort(Job x):
    return x.slope


cdef void recompute_r0(list[Job] jobs):
    cdef:
        int j
    jobs[0].r[0] = 0
    for j in range(1, len(jobs)):
        jobs[j].r[0] = jobs[j - 1].r[0] + jobs[j - 1].p[0]
