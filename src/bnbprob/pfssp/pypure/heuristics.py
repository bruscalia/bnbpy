from bnbprob.pfssp.pypure.job import Job
from bnbprob.pfssp.pypure.permutation import Permutation, start_perm
from bnbprob.pfssp.pypure.sequence import empty_sigma

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
    M = len(jobs[0].p)  # Assume r is the same size for all jobs

    # Sort jobs based on T in descending order
    jobs.sort(key=lambda job: job.T, reverse=True)

    # Initial setup for two jobs
    vec = [jobs[0], jobs[1]]
    recompute_r0(vec, 0)

    s1 = empty_sigma(M)
    for job in vec:
        s1.job_to_bottom(job)

    vec = [jobs[1], jobs[0]]
    recompute_r0(vec, 0)

    s2 = empty_sigma(M)
    for job in vec:
        s2.job_to_bottom(job)

    c1 = max(s1.C)
    c2 = max(s2.C)
    sol = s1 if c1 <= c2 else s2

    # Find best insert for every other job
    seq_size = 2
    for j in range(2, len(jobs)):
        base_sig = empty_sigma(M)
        best_cost = float('inf')

        for i in range(seq_size + 1):
            job = jobs[j]
            vec = sol.jobs.copy()
            vec.insert(i, job)
            recompute_r0(vec)

            if i > 0:
                base_sig.job_to_bottom(vec[i - 1])

            s_alt = base_sig.copy()  # Shallow copy
            for k in range(i, len(vec)):
                s_alt.job_to_bottom(vec[k])

            cost_alt = max(s_alt.C)
            if cost_alt < best_cost:
                best_cost = cost_alt
                best_sol = s_alt

        seq_size += 1
        sol = best_sol

    return Permutation(sol.m, [], sol, empty_sigma(M), len(jobs))


def local_search(jobs: list[Job]) -> Permutation:
    """Best insertion heuristic

    Parameters
    ----------
    jobs : list[Job]
        Jobs used to compose solution

    Returns
    -------
    Permutation
        Solution obtained from best move derived from base solution
    """

    M = len(jobs[0].p)

    recompute_r0(jobs)
    best_move = empty_sigma(M)
    for job in jobs:
        best_move.job_to_bottom(job)
    best_cost = max(best_move.C)

    for i in range(len(jobs)):
        base_sig = empty_sigma(M)

        for j in range(len(jobs)):
            free_jobs = jobs.copy()
            job = free_jobs.pop(i)
            free_jobs.insert(j, job)

            if j > 0:
                recompute_r0(free_jobs, j - 1)
                base_sig.job_to_bottom(free_jobs[j - 1])
            else:
                recompute_r0(free_jobs, j)

            if j == i or j == i + 1:
                continue

            s_alt = base_sig.copy()
            for k in range(j, len(free_jobs)):
                s_alt.job_to_bottom(free_jobs[k])

            new_cost = max(s_alt.C)
            if new_cost < best_cost:
                best_move = s_alt
                best_cost = new_cost

    return Permutation(best_move.m, [], best_move, empty_sigma(M), len(jobs))


def recompute_r0(jobs: list[Job], k: int = 0) -> None:
    if k == 0:
        jobs[0].r[0] = 0
        k += 1
    for j in range(k, len(jobs)):
        jobs[j].r[0] = jobs[j - 1].r[0] + jobs[j - 1].p[0]
