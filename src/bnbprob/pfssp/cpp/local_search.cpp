#include <vector>

#include "job.hpp"
#include "sigma.hpp"
#include "permutation.hpp"
#include "utils.hpp"
#include "local_search.hpp"


// A new base solution following the same sequence of the current
Permutation local_search(Permutation &perm){
    std::vector<JobPtr> vec = perm.get_sequence_copy();
    Permutation sol_base = Permutation(perm.m, vec);

    // The release date in the first machine must be recomputed
    // As positions might change
    recompute_r0(sol_base.free_jobs);
    vec = perm.get_sequence_copy();
    Permutation best_move = Permutation(perm.m, vec);
    for (int i = 0; i < best_move.free_jobs.size(); ++i){
        best_move.sigma1.job_to_bottom(best_move.free_jobs.at(i));
    }
    best_move.free_jobs = {};
    int best_cost = best_move.calc_lb_full();

    // Try to remove every job
    for (int i = 0; i < sol_base.free_jobs.size(); ++i){
        for (int j = 0; j < sol_base.free_jobs.size(); ++j){
            if (j == i || j == i + 1){
                continue;
            }
            // Here the swap is performed
            Permutation sol_alt = sol_base.copy();
            JobPtr job = sol_alt.free_jobs[i];
            sol_alt.free_jobs.erase(sol_alt.free_jobs.begin() + i);
            sol_alt.free_jobs.insert(sol_alt.free_jobs.begin() + j, job);
            // Careful recomputation althuogh it worked without it
            // probably because of memoryviews
            recompute_r0(sol_alt.free_jobs);
            // In the new solution jobs are sequentially
            // inserted in the last position, so only sigma 1 is modified
            // Updates to sigma C for each machine are automatic
            for (int k = 0; k < sol_alt.free_jobs.size(); ++k){
                sol_alt.sigma1.job_to_bottom(sol_alt.free_jobs.at(k));
            }
            sol_alt.free_jobs = {};
            int new_cost = sol_alt.calc_lb_full();
            if (new_cost < best_cost){
                best_move = std::move(sol_alt);
                best_cost = new_cost;
            }
        }
    }
    return best_move;
}
