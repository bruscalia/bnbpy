#include "local_search.hpp"

#include <vector>

#include "job.hpp"
#include "permutation.hpp"
#include "sigma.hpp"
#include "utils.hpp"

Permutation local_search(std::vector<JobPtr> &jobs_)
{
    Sigma sol_base;
    Int1DPtr M = jobs_[0]->m;  // Assume r is the same size for all jobs

    // Copy to avoid modifying inplace previous solution
    std::vector<JobPtr> jobs = copy_jobs(jobs_);

    // The release date in the first machine must be recomputed
    // As positions might change
    compute_starts_alt(jobs, *M);
    Sigma best_move = (M);
    for (int i = 0; i < jobs.size(); ++i)
    {
        best_move.job_to_bottom(jobs[i]);
    }
    int best_cost = best_move.cost();

    // Try to remove every job
    for (int i = 0; i < jobs.size(); ++i)
    {
        // Base sequence tracked in iteration
        Sigma base_sig = (M);
        base_sig.jobs.reserve(jobs.size());
        for (int j = 0; j < jobs.size(); ++j)
        {
            // Vector of free jobs
            std::vector<JobPtr> free_jobs = jobs;
            JobPtr job = std::move(free_jobs[i]);
            free_jobs.erase(free_jobs.begin() + i);
            free_jobs.insert(free_jobs.begin() + j, job);

            // Recompute release dates only of necessary jobs
            if (j > 0)
            {
                compute_starts_alt(free_jobs, *M);
                // compute_starts_alt(free_jobs, *M, j - 1);
                base_sig.job_to_bottom(free_jobs[j - 1]);
            }
            else
            {
                compute_starts_alt(free_jobs, *M);
                // compute_starts_alt(free_jobs, *M, j);
            }
            // Avoid repeated moves
            if (j == i || j == i + 1)
            {
                continue;
            }
            // Here the insertion is performed
            Sigma s_alt = (base_sig);  // Shallow copy
            for (int k = j; k < free_jobs.size(); ++k)
            {
                s_alt.job_to_bottom(free_jobs[k]);
            }

            // New cost is the greatest completion time
            int new_cost = s_alt.cost();
            if (new_cost < best_cost)
            {
                best_move = std::move(s_alt);
                best_cost = new_cost;
            }
        }
    }
    Permutation perm =
        Permutation(best_move.m, jobs.size(), jobs.size(), best_move,
                    std::vector<JobPtr>{}, Sigma(best_move.m));
    return perm;
}
