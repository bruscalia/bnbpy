#include "path_relinking.hpp"

#include <algorithm>
#include <unordered_set>
#include <vector>

#include "job.hpp"
#include "permutation.hpp"

std::unordered_set<PathSwap> find_swaps(const Permutation &perm_a,
                                        const Permutation &perm_b)
{
    std::unordered_set<PathSwap> swaps{};
    std::vector<JobPtr> jobs_a = perm_a.get_sequence_copy();
    std::vector<JobPtr> jobs_b = perm_b.get_sequence_copy();
    for (int i = 0; i < jobs_a.size(); ++i)
    {
        for (int j = 0; j < jobs_b.size(); ++j)
        {
            if (jobs_a[i]->j == jobs_b[j]->j)
            {
                swaps.insert({i, jobs_b[j]->j});
            }
        }
    }
    return swaps;
}

void apply_swap(Permutation &perm, const PathSwap &swap)
{
    // Find the position of the job with job_id
    auto it = std::find_if(perm.free_jobs.begin(), perm.free_jobs.end(),
                           [&swap](const JobPtr &job)
                           { return job->j == swap.job_id; });
    // If the job is found, swap it with the job at the specified position
    if (it != perm.free_jobs.end())
    {
        // Swap the jobs in the permutation
        std::swap(perm.free_jobs[swap.position], perm.free_jobs[swap.job_id]);
    }
}

int calc_cost(Permutation &perm)
{
    // While perm has free jobs, include job 0 to sigma 1
    while (!perm.free_jobs.empty())
    {
        perm.push_job_forward(0);
    }
    return perm.calc_lb_full();
}

Permutation path_relinking(const Permutation &a, const Permutation &b)
{
    // Placeholder for the path relinking algorithm
    // This function should implement the path relinking logic between two
    // permutations For now, we return an empty permutation
    std::unordered_set<PathSwap> swaps = find_swaps(a, b);
    Permutation sol = {a.m, a.get_sequence_copy()};

    // Edge case swaps is lesser than 2
    if (swaps.size() < 2)
    {
        calc_cost(sol);
        return sol;
    }

    // Default initialization - should return anything feasible
    // without copying original permutations
    Permutation sol_global;
    int cost = LARGE;
    int cost_global = LARGE;

    // Iterate while there are swaps to be made
    while (!swaps.empty())
    {
        // Test all swaps in a give step to choose the best one
        Permutation sol_min;
        int cost_min = LARGE;  // Arbitrary large number
        PathSwap swap_min;
        for (const auto &swap : swaps)
        {
            Permutation sol_alt = sol.copy();
            apply_swap(sol_alt, swap);
            int cost_alt = calc_cost(sol_alt);
            if (cost_alt < cost_min)
            {
                sol_min = std::move(sol_alt);
                cost_min = cost_alt;
                swap_min = std::move(swap);
            }
        }
        sol = std::move(sol_min);
        cost = cost_min;
        // Remove the swap from the set
        swaps.erase(swap_min);
        // If the new solution is better than the global best, update it
        if (cost < cost_global)
        {
            sol_global = std::move(sol);
            cost_global = cost;
        }
    }
    return sol_global;
}
