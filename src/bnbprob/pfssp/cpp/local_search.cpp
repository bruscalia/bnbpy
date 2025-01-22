#include <vector>

#include "job.hpp"
#include "sigma.hpp"
#include "permutation.hpp"
#include "utils.hpp"
#include "local_search.hpp"


Permutation local_search(std::vector<JobPtr> &jobs_){
    Sigma sol_base;

    // Copy to avoid modifying inplace previous solution
    std::vector<JobPtr> jobs = copy_jobs(jobs_);
    int M = jobs[0]->p->size();  // Assume r is the same size for all jobs

    // The release date in the first machine must be recomputed
    // As positions might change
    recompute_r0(jobs);
    Sigma best_move = (M);
    for (int i = 0; i < jobs.size(); ++i){
        best_move.job_to_bottom(jobs[i]);
    }
    int best_cost = get_max_value(best_move.C);

    // Try to remove every job
    for (int i = 0; i < jobs.size(); ++i){
        // Base sequence tracked in iteration
        Sigma base_sig = (M);
        base_sig.jobs.reserve(jobs.size());
        for (int j = 0; j < jobs.size(); ++j){
            // Vector of free jobs
            std::vector<JobPtr> free_jobs = jobs;
            JobPtr job = std::move(free_jobs[i]);
            free_jobs.erase(free_jobs.begin() + i);
            free_jobs.insert(free_jobs.begin() + j, job);
            if (j > 0){
                recompute_r0(free_jobs, j - 1);
                base_sig.job_to_bottom(free_jobs[j - 1]);
            } else {
                recompute_r0(free_jobs, j);
            }
            // Avoid repeated moves
            if (j == i || j == i + 1){
                continue;
            }
            // Here the insertion is performed
            Sigma s_alt = (base_sig);  // Shallow copy
            for (int k = j; k < free_jobs.size(); ++k){
                s_alt.job_to_bottom(free_jobs[k]);
            }
            int new_cost = get_max_value(s_alt.C);
            if (new_cost < best_cost){
                best_move = std::move(s_alt);
                best_cost = new_cost;
            }
        }
    }
    Permutation perm = Permutation(
        best_move.m, jobs.size(), jobs.size(), best_move,
        std::vector<JobPtr>{}, Sigma(best_move.m));
    return perm;
}
