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
    // Initialize random number generator
    std::mt19937 generator(seed);
    return ils_destruction(sigma, d, generator);
}

ILSDestruction ils_destruction(Sigma sigma, int d, std::mt19937 generator)
{

    ILSDestruction result;
    result.sigma = Sigma(sigma.m);
    std::vector<JobPtr> alloc_jobs = copy_jobs(sigma.jobs);
    std::vector<JobPtr> free_jobs{};
    free_jobs.reserve(d);

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

Permutation ils(std::vector<JobPtr> &jobs, const int &max_iter)
{
    // Initialize variables for ILS
    int d = jobs.size() / 10; // Destruction size
    int max_age = jobs.size(); // Maximum age before restart
    return ils(jobs, max_iter, d, max_age, 42);

}

Permutation ils(std::vector<JobPtr> &jobs, const int &max_iter, const int &seed)
{
    // Initialize variables for ILS
    int d = jobs.size() / 10; // Destruction size
    int max_age = jobs.size(); // Maximum age before restart

    return ils(jobs, max_iter, d, max_age, seed);
}

Permutation ils(std::vector<JobPtr> &jobs, const int &max_iter, const int &d, const int &seed)
{
    // Initialize variables for ILS
    int max_age = jobs.size(); // Maximum age before restart

    return ils(jobs, max_iter, d, max_age, seed);
}

Permutation ils(std::vector<JobPtr> &jobs, const int &max_iter, const int &d, const int &max_age,
                const int &seed)
{
    // Initial solution with NEH + best move local search
    Permutation perm = neh_constructive(jobs);
    perm = local_search(perm.get_sequence_copy());

    // Initialize variables for ILS
    int age_improv = 0; // Age of improvement

    Permutation best_perm = perm.copy();
    Permutation ref_perm = perm.copy();
    int best_cost = best_perm.calc_lb_full();
    int ref_cost = best_cost;

    // Generator to randomize the solution
    std::mt19937 generator(seed);
    std::uniform_real_distribution<> dist(0.0, 1.0);

    // ILS
    for (int i = 0; i < max_iter; ++i)
    {

        // Destruction phase
        ILSDestruction destruction = ils_destruction(ref_perm.sigma1, d, generator);
        Sigma sigma1 = destruction.sigma;
        std::vector<JobPtr> free_jobs = destruction.jobs;

        // Intensification phase
        Sigma new_sigma = neh_body(sigma1, free_jobs);

        // Local search phase
        Permutation new_perm = local_search(new_sigma.jobs);
        int new_cost = new_perm.calc_lb_full();

        if (new_cost < best_cost)
        {
            best_perm = std::move(new_perm);
            best_cost = new_cost;
            ref_perm = best_perm.copy();
            ref_cost = best_cost;
            age_improv = 0; // Reset age of improvement
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

        // Update the age of improvement
        if (age_improv >= max_age)
        {
            break;
        }
        age_improv++;
    }

    return best_perm;
}
