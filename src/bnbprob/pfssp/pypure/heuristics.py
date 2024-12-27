from bnbprob.pfssp.pypure.job import Job
from bnbprob.pfssp.pypure.permutation import Permutation, start_perm

LARGE_INT = 10000000


def quick_constructive(jobs: list[Job]) -> Permutation:
    """Computes a feasible solution based on the sorting
    strategy by Palmer (1965).

    Parameters
    ----------
    jobs : list[Job]
        Jobs used to compose solution

    Returns
    -------
    Permutation
        New feasible solution

    References
    ----------
    Palmer, D. S. (1965). Sequencing jobs through a multi-stage process
    in the minimum total time—a quick method of obtaining a near optimum.
    Journal of the Operational Research Society, 16(1), 101-107
    """
    M = len(jobs[0].p)
    sol = start_perm(M, jobs)
    sol.free_jobs.sort(key=lambda x: x.slope, reverse=True)
    for _ in range(len(sol.free_jobs)):
        job = sol.free_jobs.pop(0)
        sol.sigma1.job_to_bottom(job)
    return sol


def neh_constructive(jobs: list[Job]) -> Permutation:
    """Constructive heuristic of Nawaz et al. (1983) based
    on best-insertion of jobs sorted according to total processing
    time in descending order.

    Parameters
    ----------
    jobs : list[Job]
        Jobs used to compose solution

    Returns
    -------
    Permutation
        New feasible solution

    Reference
    ---------
    Nawaz, M., Enscore Jr, E. E., & Ham, I. (1983).
    A heuristic algorithm for the m-machine,
    n-job flow-shop sequencing problem.
    Omega, 11(1), 91-95.
    """

    # Find best order of two jobs with longest processing times
    jobs.sort(key=lambda x: x.T, reverse=True)
    M = len(jobs[0].p)

    vec = [jobs[0].copy(), jobs[1].copy()]
    s1 = start_perm(M, vec)
    for _ in range(len(s1.free_jobs)):
        job_i = s1.free_jobs.pop(0)
        s1.sigma1.job_to_bottom(job_i)

    vec = [jobs[1].copy(), jobs[0].copy()]
    s2 = start_perm(M, vec)
    for _ in range(len(s2.free_jobs)):
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
        best_sol = None
        # Positions in sequence
        for i in range(seq_size + 1):
            s_alt = start_perm(sol.m, sol.get_sequence_copy())
            job = jobs[j]
            s_alt.free_jobs.insert(i, job.copy())
            # Fix all jobs
            for _ in range(len(s_alt.free_jobs)):
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


def local_search(perm: Permutation) -> Permutation:
    """Best insertion heuristic

    Parameters
    ----------
    perm : Permutation
        Base Solution

    Returns
    -------
    Permutation
        Solution obtained from best move derived from base solution
    """

    # A new base solution following the same sequence of the current
    sol_base = start_perm(perm.m, perm.get_sequence_copy())

    # The release date in the first machine must be recomputed
    # As positions might change
    recompute_r0(sol_base.free_jobs)
    best_move = start_perm(perm.m, perm.get_sequence_copy())
    for _ in range(len(best_move.free_jobs)):
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
            recompute_r0(sol_alt.free_jobs)

            # In the new solution jobs are sequentially
            # inserted in the last position, so only sigma 1 is modified
            # Updates to sigma C for each machine are automatic
            for _ in range(len(sol_alt.free_jobs)):
                job = sol_alt.free_jobs.pop(0)
                sol_alt.sigma1.job_to_bottom(job)

            # New bound is computed considering sigma C
            new_cost = sol_alt.calc_bound()
            if new_cost < best_cost:
                best_move = sol_alt
                best_cost = new_cost

    return best_move


def recompute_r0(jobs: list[Job]) -> None:
    jobs[0].r[0] = 0
    for j in range(1, len(jobs)):
        jobs[j].r[0] = jobs[j - 1].r[0] + jobs[j - 1].p[0]
