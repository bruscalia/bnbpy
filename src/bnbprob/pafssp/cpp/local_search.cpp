#include "local_search.hpp"

#include <climits>
#include <vector>

#include "job.hpp"
#include "permutation.hpp"
#include "sigma.hpp"
#include "utils.hpp"

// Find the best move for the current jobs, return SearchState
SearchState ls_best_move(const std::vector<JobPtr>& jobs_,
                         const std::shared_ptr<MachineGraph>& mach_graph)
{
    int M = jobs_[0]->p->size();
    // Safeguard
    std::vector<JobPtr> jobs = copy_reset(jobs_, *mach_graph);
    // Initialize search state
    SearchState best(jobs, INT_MAX);

    for (unsigned int i = 0; i < jobs.size(); ++i)
    {
        // Initialize the base sequence
        std::vector<JobPtr> free_jobs = jobs;
        JobPtr job = std::move(free_jobs[i]);
        free_jobs.erase(free_jobs.begin() + i);

        // Initialize two-way sigmas
        // Initialize lists of sigma foward and backward
        int seq_size = free_jobs.size();
        std::vector<Sigma> sigma_fwd(seq_size + 1);
        std::vector<Sigma> sigma_bwd(seq_size + 1);
        sigma_fwd[0] = Sigma(M, mach_graph);
        sigma_bwd[seq_size] = Sigma(M, mach_graph);
        // Gradually complete the sigmas
        // Each sigma is a shallow copy of the previous one with one job more
        for (int j = 0; j < seq_size; ++j)
        {
            sigma_fwd[j + 1] = sigma_fwd[j];  // Shallow copy
            sigma_fwd[j + 1].job_to_bottom(free_jobs[j]);
        }
        for (int j = seq_size; j > 0; --j)
        {
            sigma_bwd[j - 1] = sigma_bwd[j];  // Shallow copy
            sigma_bwd[j - 1].job_to_top(free_jobs[j - 1]);
        }

        // Now try to insert in every position
        for (int j = 0; j <= seq_size; ++j)
        {
            // Insert job in position j
            sigma_fwd[j].job_to_bottom(job);
            int new_cost = get_max_value(sigma_fwd[j].C, sigma_bwd[j].C);
            if (new_cost < best.cost)
            {
                std::vector<JobPtr> s_alt = sigma_fwd[j].jobs;  // Shallow copy
                for (JobPtr& j2 : sigma_bwd[j].jobs)
                {
                    s_alt.push_back(j2);
                }
                best = SearchState(s_alt, new_cost);
            }
        }
    }
    return best;
}

Permutation local_search(std::vector<JobPtr>& jobs_,
                         const std::shared_ptr<MachineGraph>& mach_graph)
{
    std::vector<JobPtr> jobs = copy_reset(jobs_, *mach_graph);
    int M = jobs[0]->p->size();
    // Empty initialization
    SearchState state(jobs, INT_MAX);

    // Local search loop
    for (int k = 0; k < 1000; ++k)
    {
        SearchState next = ls_best_move(state.jobs, mach_graph);
        if (next.cost < state.cost)
        {
            state = std::move(next);
        }
        else
        {
            break;
        }
    }
    Sigma sigma1(M, mach_graph);
    for (JobPtr& jp : state.jobs)
    {
        sigma1.job_to_bottom(jp);
    }
    Permutation perm =
        Permutation(M, jobs.size(), jobs.size(), sigma1, std::vector<JobPtr>{},
                    Sigma(sigma1.m, mach_graph), mach_graph);
    return perm;
}
