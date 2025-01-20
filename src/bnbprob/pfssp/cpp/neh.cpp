#include <algorithm>
#include <vector>

#include "job.hpp"
#include "permutation.hpp"
#include "sigma.hpp"
#include "utils.hpp"
#include "neh.hpp"


inline bool desc_T(const JobPtr& a, const JobPtr& b) { return b->T < a->T; }

Permutation neh_constructive(std::vector<JobPtr>& jobs) {
    int j, i, k, M, best_cost, seq_size, cost_alt;
    // Sigma s1, s2, sol, best_sol, s_alt;
    JobPtr job;
    std::vector<JobPtr> vec;

    // Find best order of two jobs with longest processing times
    std::sort(jobs.begin(), jobs.end(), desc_T);
    M = jobs[0]->p->size();  // Assume r is the same size for all jobs

    // Initial setup for two jobs
    vec.resize(2);
    vec[0] = jobs[0];
    vec[1] = jobs[1];
    Sigma s1 = Sigma(M);
    for (int k = 0; k < vec.size(); ++k) {
        s1.job_to_bottom(vec[k]);
    }

    vec[0] = jobs[1];
    vec[1] = jobs[0];
    Sigma s2 = Sigma(M);
    for (int k = 0; k < vec.size(); ++k) {
        s2.job_to_bottom(vec[k]);
    }

    int c1 = get_max_value(s1.C);
    int c2 = get_max_value(s2.C);
    Sigma sol;
    if (c1 <= c2) {
        sol = std::move(s1);
    } else {
        sol = std::move(s2);
    }

    // Find best insert for every other job
    seq_size = 2;
    for (j = 2; j < jobs.size(); ++j) {
        best_cost = INT_MAX;  // Replace with LARGE_INT constant
        Sigma best_sol;
        for (i = 0; i <= seq_size; ++i) {
            job = jobs[j];
            vec = copy_jobs(sol.jobs);
            vec.insert(vec.begin() + i, job);
            recompute_r0(vec);
            Sigma s_alt = Sigma(M);
            for (k = 0; k < vec.size(); ++k) {
                s_alt.job_to_bottom(vec[k]);
            }
            cost_alt = get_max_value(s_alt.C);
            if (cost_alt < best_cost) {
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
