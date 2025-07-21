#include "neh.hpp"

#include <algorithm>
#include <climits>
#include <vector>

#include "job.hpp"
#include "permutation.hpp"
#include "sigma.hpp"
#include "utils.hpp"

inline bool desc_T(const JobPtr& a, const JobPtr& b)
{
    return b->get_T() < a->get_T();
}

Permutation neh_constructive(std::vector<JobPtr>& jobs)
{
    // Find best order of two jobs with longest processing times
    std::sort(jobs.begin(), jobs.end(), desc_T);

    return neh_core(jobs);
}

Permutation neh_core(std::vector<JobPtr>& jobs)
{
    int j, i, k, M, c1, c2, best_cost, seq_size, cost_alt;
    // Sigma s1, s2, sol, best_sol, s_alt;
    JobPtr job;
    std::vector<JobPtr> vec;
    Sigma s1, s2, sol, best_sol;

    M = jobs[0]->p->size();  // Assume r is the same size for all jobs

    // Initial setup for two jobs
    vec.resize(2);
    vec[0] = jobs[0];
    vec[1] = jobs[1];
    recompute_r0(vec, 0);
    s1 = (M);
    s1.jobs.reserve(2);
    for (int k = 0; k < vec.size(); ++k)
    {
        s1.job_to_bottom(vec[k]);
    }

    vec[0] = jobs[1];
    vec[1] = jobs[0];
    recompute_r0(vec, 0);
    s2 = (M);
    s2.jobs.reserve(2);
    for (int k = 0; k < vec.size(); ++k)
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
    seq_size = 2;
    for (j = 2; j < jobs.size(); ++j)
    {
        Sigma base_sig(M);
        best_cost = INT_MAX;  // Replace with LARGE_INT constant
        for (i = 0; i <= seq_size; ++i)
        {
            // Insert job in position i
            job = jobs[j];
            vec = copy_jobs(sol.jobs);
            vec.insert(vec.begin() + i, std::move(job));
            recompute_r0(vec);

            // Recompute release dates only of necessary jobs
            if (i > 0)
            {
                base_sig.job_to_bottom(vec[i - 1]);
            }

            // Here the insertion is performed
            Sigma s_alt = (base_sig);  // Shallow copy
            s_alt.jobs.reserve(vec.size());
            for (int k = i; k < vec.size(); ++k)
            {
                s_alt.job_to_bottom(vec[k]);
            }

            // New cost is the greatest completion time
            cost_alt = get_max_value(s_alt.C);
            if (cost_alt < best_cost)
            {
                best_cost = cost_alt;
                best_sol = std::move(s_alt);
            }
        }
        seq_size += 1;
        sol = std::move(best_sol);
    }
    Permutation perm = Permutation(sol.m, jobs.size(), jobs.size(), sol,
                                   std::vector<JobPtr>{}, Sigma(sol.m));
    return perm;
}
