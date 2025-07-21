#include "randomized_heur.hpp"

#include <algorithm>
#include <limits>
#include <random>

#include "job.hpp"
#include "local_search.hpp"
#include "neh.hpp"

Permutation randomized_heur(std::vector<JobPtr> jobs_, int n_iter,
                            unsigned int seed)
{
    Permutation best_perm;
    int best_cost = std::numeric_limits<int>::max();
    std::mt19937 g;
    if (seed == 0)
    {
        std::random_device rd;
        g.seed(rd());
    }
    else
    {
        g.seed(seed);
    }

    for (int iter = 0; iter < n_iter; ++iter)
    {
        std::vector<JobPtr> jobs = copy_jobs(jobs_);
        std::shuffle(jobs.begin(), jobs.end(), g);
        Permutation perm = neh_core(jobs);
        int cost = perm.calc_lb_full();
        // Local search until no improvement
        for (int k = 0; k < 10000; k++)
        {
            Permutation new_perm = local_search(perm.get_sequence_copy());
            int new_cost = new_perm.calc_lb_full();
            if (new_cost < cost)
            {
                perm = std::move(new_perm);
                cost = new_cost;
            }
            else
            {
                break;
            }
        }
        if (cost < best_cost)
        {
            best_perm = std::move(perm);
            best_cost = cost;
        }
    }
    return best_perm;
}
