#include "local_search.hpp"

#include <climits>
#include <vector>

#include "job.hpp"
#include "permutation.hpp"
#include "sigma.hpp"
#include "utils.hpp"

// Find the best move for the current jobs, return SearchState
SearchState ls_best_move(const std::vector<JobPtr>& jobs)
{
    int M = jobs[0]->p->size();
    SearchState best(Sigma(M), INT_MAX);

    for (int i = 0; i < static_cast<int>(jobs.size()); ++i)
    {
        Sigma base_sig(M);
        base_sig.jobs.reserve(jobs.size());
        for (int j = 0; j < static_cast<int>(jobs.size()); ++j)
        {
            std::vector<JobPtr> free_jobs = jobs;
            JobPtr job = std::move(free_jobs[i]);
            free_jobs.erase(free_jobs.begin() + i);
            free_jobs.insert(free_jobs.begin() + j, job);

            if (j > 0)
            {
                recompute_r0(free_jobs, j - 1);
                base_sig.job_to_bottom(free_jobs[j - 1]);
            }
            else
            {
                recompute_r0(free_jobs, j);
            }
            if (j == i || j == i + 1)
            {
                continue;
            }
            Sigma s_alt = base_sig;
            for (int k = j; k < static_cast<int>(free_jobs.size()); ++k)
            {
                s_alt.job_to_bottom(free_jobs[k]);
            }
            int new_cost = get_max_value(s_alt.C);
            if (new_cost < best.cost)
            {
                best = SearchState(s_alt, new_cost);
            }
        }
    }
    return best;
}

Permutation local_search(std::vector<JobPtr>& jobs_)
{
    std::vector<JobPtr> jobs = copy_jobs(jobs_);
    int M = jobs[0]->p->size();
    recompute_r0(jobs);
    SearchState state(Sigma(M), INT_MAX);

    // Initial state
    Sigma best_move_sigma(M);
    for (int i = 0; i < static_cast<int>(jobs.size()); ++i)
    {
        best_move_sigma.job_to_bottom(jobs[i]);
    }
    int best_cost = get_max_value(best_move_sigma.C);
    state = SearchState(best_move_sigma, best_cost);

    // Local search loop
    for (int k = 0; k < 1000; ++k)
    {
        SearchState next = ls_best_move(jobs);
        if (next.cost < state.cost)
        {
            state = next;
            // Update jobs to match the new sigma order
            jobs = next.sigma.jobs;
        }
        else
        {
            break;
        }
    }
    Permutation perm =
        Permutation(state.sigma.m, jobs.size(), jobs.size(), state.sigma,
                    std::vector<JobPtr>{}, Sigma(state.sigma.m));
    return perm;
}
