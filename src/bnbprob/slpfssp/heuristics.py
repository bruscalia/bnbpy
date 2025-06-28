from bnbprob.slpfssp.job import Job
from bnbprob.slpfssp.permutation import Permutation
from bnbprob.slpfssp.sigma import empty_sigma

LARGE_INT = 10000000


def neh_constructive_sl(jobs: list[Job]) -> Permutation:
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
    M = [len(pi) for pi in jobs[0].p]  # Assume r is the same size for all jobs

    # Sort jobs based on T in descending order
    jobs.sort(key=lambda job: job.T, reverse=True)

    # Initial setup for two jobs
    vec = [jobs[0], jobs[1]]
    compute_starts(vec, M)
    # recompute_r0(vec, 0)

    s1 = empty_sigma(M)
    for job in vec:
        s1.job_to_bottom(job)

    vec = [jobs[1], jobs[0]]
    compute_starts(vec, M)
    # recompute_r0(vec, 0)

    s2 = empty_sigma(M)
    for job in vec:
        s2.job_to_bottom(job)

    c1 = s1.cost
    c2 = s2.cost
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
            compute_starts(vec, M)
            # recompute_r0(vec)

            if i > 0:
                base_sig.job_to_bottom(vec[i - 1])

            s_alt = base_sig.copy()  # Shallow copy
            for k in range(i, len(vec)):
                s_alt.job_to_bottom(vec[k])

            cost_alt = s_alt.cost
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

    M = [len(pi) for pi in jobs[0].p]  # Assume r is the same size for all jobs

    compute_starts(jobs, M)
    best_move = empty_sigma(M)
    for job in jobs:
        best_move.job_to_bottom(job)
    best_cost = best_move.cost

    for i in range(len(jobs)):
        base_sig = empty_sigma(M)

        for j in range(len(jobs)):
            free_jobs = jobs.copy()
            job = free_jobs.pop(i)
            free_jobs.insert(j, job)

            if j > 0:
                # recompute_r0(free_jobs, j - 1)
                compute_starts(free_jobs, M)
                base_sig.job_to_bottom(free_jobs[j - 1])
            else:
                # recompute_r0(free_jobs, j)
                compute_starts(free_jobs, M)

            if j == i or j == i + 1:
                continue

            s_alt = base_sig.copy()
            for k in range(j, len(free_jobs)):
                s_alt.job_to_bottom(free_jobs[k])

            new_cost = s_alt.cost
            if new_cost < best_cost:
                best_move = s_alt
                best_cost = new_cost

    return Permutation(best_move.m, [], best_move, empty_sigma(M), len(jobs))


def recompute_r0(jobs: list[Job], k: int = 0) -> None:
    if k == 0:
        for sl in range(len(jobs[0].p)):
            jobs[0].r[sl][0] = 0
        k += 1
    for j in range(k, len(jobs)):
        for sl in range(len(jobs[j].p)):
            jobs[j].r[sl][0] = jobs[j - 1].r[sl][0] + jobs[j - 1].p[sl][0]


def compute_starts(seq: list[Job], m: list[int]) -> None:
    for j in range(len(seq)):
        job = seq[j]
        for sl, m_sl in enumerate(m):
            job.r[sl] = [0] * m_sl

    job = seq[0]
    for sl, m_sl in enumerate(m):
        for m_ in range(1, m_sl):
            job.r[sl][m_] = job.r[sl][m_ - 1] + job.p[sl][m_ - 1]

    for j in range(1, len(seq)):
        job = seq[j]
        prev = seq[j - 1]
        for sl, m_sl in enumerate(m):
            job.r[sl][0] = prev.r[sl][0] + prev.p[sl][0]
            for m_ in range(1, m_sl):  # TODO: ajust for reconciliation machines
                job.r[sl][m_] = max(
                    job.r[sl][m_ - 1] + job.p[sl][m_ - 1],
                    prev.r[sl][m_] + prev.p[sl][m_]
                )
