#include "ils.hpp"

#include <algorithm>
#include <random>
#include <vector>

#include "job.hpp"
#include "local_search.hpp"
#include "neh.hpp"
#include "permutation.hpp"
#include "sigma.hpp"

ILSDestruction ils_destruction(Sigma sigma, int d, int seed)
{
    ILSDestruction result;
    result.sigma = Sigma(sigma.m);
    std::vector<JobPtr> alloc_jobs = copy_jobs(sigma.jobs);
    std::vector<JobPtr> free_jobs{};
    free_jobs.reserve(d);

    std::mt19937 generator(seed);

    // Destruction phase
    for (int i = 0; i < d; ++i)
    {
        // Randomly remove a job from the solution
        std::uniform_int_distribution<int> dist(0, alloc_jobs.size() - 1);
        int job_index = dist(generator);
        free_jobs.push_back(alloc_jobs[job_index]);
        alloc_jobs.erase(alloc_jobs.begin() + job_index);
    }

    // Store jobs in sigma
    for (const auto& job : alloc_jobs)
    {
        result.sigma.job_to_bottom(job);
    }

    result.jobs = free_jobs;

    return result;
}

Permutation ils(std::vector<JobPtr>& jobs, int max_iter)
{
    // Initial solution with NEH
    Permutation perm = neh_constructive(jobs);
    for (int i = 0; i < 1000; ++i)
    {
        // Local search to improve the solution
        Permutation new_perm = local_search(perm.get_sequence_copy());
        int new_cost = new_perm.calc_lb_full();
        if (new_cost < perm.calc_lb_full())
        {
            perm = std::move(new_perm);
        }
        else
        {
            break;  // Stop if no improvement is found
        }
    }

    Permutation best_perm = perm.copy();
    Permutation ref_perm = perm.copy();
    int best_cost = best_perm.calc_lb_full();
    int ref_cost = best_cost;

    // ILS
    for (int i = 0; i < max_iter; ++i)
    {
        // Generator
        std::mt19937 generator(i);
        std::uniform_real_distribution<> dist(0.0, 1.0); // Uniform distribution from 0.0 to 1.0

        // Destruction phase
        ILSDestruction destruction = ils_destruction(ref_perm.sigma1, 5, i);
        Sigma sigma1 = destruction.sigma;
        std::vector<JobPtr> free_jobs = destruction.jobs;

        // Intensification phase
        Sigma new_sigma = neh_body(sigma1, free_jobs);

        // Local search phase
        Permutation new_perm = local_search(new_sigma.jobs);

        int new_cost = new_perm.calc_lb_full();
        for (int k = 0; k < 1000; ++k)
        {
            // Local search to improve the solution
            Permutation alt_perm = local_search(new_perm.get_sequence_copy());
            int alt_cost = alt_perm.calc_lb_full();
            if (alt_cost < new_cost)
            {
                new_perm = std::move(alt_perm);
                new_cost = alt_cost;
            }
            else if (alt_cost == new_cost &&
                     alt_perm.calc_idle_time() < new_perm.calc_idle_time())
            {
                // Prefer solutions with less idle time
                new_perm = std::move(alt_perm);
            }
            else
            {
                break;  // Stop if no improvement is found
            }
        }
        if (new_cost < best_cost)
        {
            best_perm = std::move(new_perm);
            best_cost = new_cost;
            ref_perm = best_perm.copy();
            ref_cost = best_cost;
        }
        // Accept if exponential of negative delta in costs
        // is lesser than random float
        else if (new_cost < ref_cost)
        {
            // Accept the new solution
            ref_perm = std::move(new_perm);
            ref_cost = new_cost;
        }
        else if (std::exp((ref_cost - new_cost) / 0.5) >
                   dist(generator))
        {
            // Accept the new solution with some probability
            ref_perm = std::move(new_perm);
            ref_cost = new_cost;
        }
    }

    return best_perm;
}
