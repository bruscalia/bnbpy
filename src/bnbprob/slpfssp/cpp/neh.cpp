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
    std::sort(jobs.begin(), jobs.end(), desc_T);
    return neh_core(jobs);
}

Permutation neh_core(std::vector<JobPtr>& jobs)
{
    int M = jobs[0]->m->size();
    std::vector<JobPtr> vec(2);
    Sigma s1(jobs[0]->m), s2(jobs[0]->m);

    // Try both orders for the first two jobs
    vec[0] = jobs[0];
    vec[1] = jobs[1];
    compute_starts_alt(vec, *jobs[0]->m);
    s1.jobs.reserve(2);
    for (int k = 0; k < 2; ++k) s1.job_to_bottom(vec[k]);

    vec[0] = jobs[1];
    vec[1] = jobs[0];
    compute_starts_alt(vec, *jobs[0]->m);
    s2.jobs.reserve(2);
    for (int k = 0; k < 2; ++k) s2.job_to_bottom(vec[k]);

    int c1 = s1.cost();
    int c2 = s2.cost();
    Sigma sol = (c1 <= c2) ? std::move(s1) : std::move(s2);

    // Remaining jobs
    std::vector<JobPtr> free_jobs(jobs.begin() + 2, jobs.end());
    sol = neh_body(sol, free_jobs);

    Permutation perm(sol.m, jobs.size(), jobs.size(), sol,
                     std::vector<JobPtr>{}, Sigma(sol.m));
    return perm;
}

Sigma neh_body(Sigma sol, std::vector<JobPtr>& jobs)
{
    int M = jobs[0]->m->size();
    int seq_size = sol.jobs.size();
    for (int j = 0; j < jobs.size(); ++j)
    {
        Sigma base_sig(sol.m);
        int best_cost = INT_MAX;
        Sigma best_sol;
        for (int i = 0; i <= seq_size; ++i)
        {
            JobPtr job = jobs[j];
            std::vector<JobPtr> vec = copy_jobs(sol.jobs);
            vec.insert(vec.begin() + i, job);
            compute_starts_alt(vec, *sol.m);

            if (i > 0) base_sig.job_to_bottom(vec[i - 1]);

            Sigma s_alt(base_sig);
            s_alt.jobs.reserve(vec.size());
            for (int k = i; k < vec.size(); ++k) s_alt.job_to_bottom(vec[k]);

            int cost_alt = s_alt.cost();
            if (cost_alt < best_cost)
            {
                best_cost = cost_alt;
                best_sol = std::move(s_alt);
            }
        }
        ++seq_size;
        sol = std::move(best_sol);
    }
    return sol;
}
