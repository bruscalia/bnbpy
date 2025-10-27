#include "neh.hpp"

#include <algorithm>
#include <climits>
#include <vector>

#include "job.hpp"
#include "permutation.hpp"
#include "sigma.hpp"
#include "utils.hpp"

Permutation neh_initialization(std::vector<JobPtr>& jobs,
                             const std::shared_ptr<MachineGraph>& mach_graph)
{
    // Find best order of two jobs with longest processing times
    std::sort(jobs.begin(), jobs.end(), desc_T);

    return neh_core(jobs, mach_graph);
}

Permutation neh_core(std::vector<JobPtr>& jobs_,
                     const std::shared_ptr<MachineGraph>& mach_graph)
{
    int M, c1, c2;
    // Sigma s1, s2, sol, best_sol, s_alt;
    std::vector<JobPtr> vec;
    Sigma s1, s2, sol, best_sol;
    std::vector<JobPtr> jobs = jobs_;

    M = jobs[0]->p.size();  // Assume r is the same size for all jobs

    // Initial setup for two jobs
    vec.resize(2);
    vec[0] = jobs[0];
    vec[1] = jobs[1];
    s1 = Sigma(M, mach_graph);
    for (unsigned int k = 0; k < vec.size(); ++k)
    {
        s1.job_to_bottom(vec[k]);
    }

    vec[0] = jobs[1];
    vec[1] = jobs[0];
    s2 = Sigma(M, mach_graph);
    for (unsigned int k = 0; k < vec.size(); ++k)
    {
        s2.job_to_bottom(vec[k]);
    }

    c1 = get_max_value(s1.C);
    c2 = get_max_value(s2.C);
    if (c1 <= c2)
    {
        sol = std::move(s1);
    }
    else
    {
        sol = std::move(s2);
    }

    // Find best insert for every other job
    std::vector<JobPtr> free_jobs = std::vector<JobPtr>(jobs.begin() + 2, jobs.end());

    std::vector<JobPtr> solution_jobs = neh_body(sol.get_jobs(), free_jobs, mach_graph);

    // Create final Sigma from solution jobs
    Sigma final_sol(M, mach_graph);
    for (JobPtr& job : solution_jobs) {
        final_sol.job_to_bottom(job);
    }

    // Prepare as a permutation
    Permutation perm =
        Permutation(final_sol.m, jobs.size(), jobs.size(), final_sol, std::vector<JobPtr>{},
                    Sigma(final_sol.m, mach_graph), mach_graph);
    return perm;
}

std::vector<JobPtr> neh_body(std::vector<JobPtr> sol_jobs, std::vector<JobPtr> &jobs,
                             const std::shared_ptr<MachineGraph> &mach_graph)
{
    unsigned int j, i, best_cost, seq_size, cost_alt;
    const int M = jobs[0]->p.size();  // Assume r is the same size for all jobs
    JobPtr job;
    std::vector<JobPtr> vec;
    std::vector<JobPtr> best_sol_jobs;

    // Find best insert for every other job
    seq_size = sol_jobs.size();
    for (j = 0; j < jobs.size(); ++j)
    {
        best_cost = INT_MAX;  // Replace with LARGE_INT constant
        vec = sol_jobs;
        // Ensure r of all machines without predecessors is zero
        // Same for q of all machines without successors
        // Initialize lists of sigma foward and backward
        std::vector<Sigma> sigma_fwd(seq_size + 1);
        std::vector<Sigma> sigma_bwd(seq_size + 1);
        sigma_fwd[0] = Sigma(M, mach_graph);
        sigma_bwd[seq_size] = Sigma(M, mach_graph);
        // Gradually complete the sigmas
        // Each sigma is a shallow copy of the previous one with one job more
        for (i = 0; i < seq_size; ++i)
        {
            sigma_fwd[i + 1] = sigma_fwd[i];  // Shallow copy
            sigma_fwd[i + 1].job_to_bottom(vec[i]);
        }
        for (i = seq_size; i > 0; --i)
        {
            sigma_bwd[i - 1] = sigma_bwd[i];  // Shallow copy
            sigma_bwd[i - 1].job_to_top(vec[i - 1]);
        }
        // Each combination should append job to sigma 1 and take cost from
        // a pair sigma 1 and sigma 2
        for (i = 0; i <= seq_size; ++i)
        {
            // Insert job in position i
            job = jobs[j];
            // Append job to sigma 1
            sigma_fwd[i].job_to_bottom(job);
            // Take cost from sigma 1 and sigma 2
            cost_alt = get_max_value(sigma_fwd[i].C, sigma_bwd[i].C);
            if (cost_alt < best_cost)
            {
                best_sol_jobs = sigma_fwd[i].get_jobs();  // Shallow copy

                for (JobPtr& j2 : sigma_bwd[i].get_jobs())
                {
                    best_sol_jobs.push_back(j2);
                }
                best_cost = cost_alt;
                best_sol_jobs = best_sol_jobs;
            }
        }
        seq_size += 1;
        sol_jobs = best_sol_jobs;
    }
    return sol_jobs;
}
