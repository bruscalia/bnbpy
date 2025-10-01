#include "local_search.hpp"

#include <climits>
#include <vector>

#include "job.hpp"
#include "permutation.hpp"
#include "sigma.hpp"
#include "utils.hpp"

// Find the best move for the current jobs, return SearchState
SearchState ls_best_move(const std::vector<JobPtr>& jobs,
                         const std::shared_ptr<MachineGraph>& mach_graph)
{
    int M = jobs[0]->p->size();
    // TODO: Update SearchState and Sigma to support initialization from
    // MachineGraph
    SearchState best(Sigma(M, mach_graph), INT_MAX);

    for (int i = 0; i < static_cast<int>(jobs.size()); ++i)
    {
        // TODO: Update Sigma to support initialization from MachineGraph
        Sigma base_sig(M, mach_graph);
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
            // TODO: Update Sigma to support initialization from MachineGraph
            Sigma s_alt = base_sig;
            for (int k = j; k < free_jobs.size(); ++k)
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

Permutation local_search(std::vector<JobPtr>& jobs_,
                         const std::shared_ptr<MachineGraph>& mach_graph)
{
    std::vector<JobPtr> jobs = copy_jobs(jobs_);
    int M = jobs[0]->p->size();
    recompute_r0(jobs);
    // TODO: Update SearchState and Sigma to support initialization from
    // MachineGraph
    SearchState state(Sigma(M, mach_graph), INT_MAX);

    // Initial state
    // TODO: Update Sigma to support initialization from MachineGraph
    Sigma best_move_sigma(M, mach_graph);
    for (int i = 0; i < static_cast<int>(jobs.size()); ++i)
    {
        best_move_sigma.job_to_bottom(jobs[i]);
    }
    int best_cost = get_max_value(best_move_sigma.C);
    state = SearchState(best_move_sigma, best_cost);

    // Local search loop
    for (int k = 0; k < 1000; ++k)
    {
        SearchState next = ls_best_move(jobs, mach_graph);
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
    Permutation perm = Permutation(
        state.sigma.m, jobs.size(), jobs.size(), state.sigma,
        std::vector<JobPtr>{}, Sigma(state.sigma.m, mach_graph), mach_graph);
    return perm;
}
