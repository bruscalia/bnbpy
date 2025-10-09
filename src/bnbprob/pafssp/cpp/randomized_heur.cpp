#include "randomized_heur.hpp"

#include <algorithm>
#include <limits>
#include <random>

#include "job.hpp"
#include "local_search.hpp"
#include "neh.hpp"

Permutation randomized_heur(std::vector<Job> jobs_, int n_iter,
                            unsigned int seed,
                            const std::shared_ptr<MachineGraph> &mach_graph)
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

    // In the first iteration, the order is the original from NEH
    best_perm = neh_core(jobs_, mach_graph);

    for (int iter = 0; iter < n_iter; ++iter)
    {
        std::vector<Job> jobs = jobs_;  // Deep copy
        if (iter > 0)
        {
            std::shuffle(jobs.begin(), jobs.end(), g);
        }
        else
        {
            // Regular NEH order
            std::sort(jobs.begin(), jobs.end(), desc_T);
        }
        // Best insertion from presorted jobs in O(m n2)
        Permutation perm = neh_core(jobs, mach_graph);
        // Local search until no improvement (sequence will be copied inside)
        std::vector<Job> sequence_copy = perm.get_sequence();
        Permutation new_perm = local_search(sequence_copy, mach_graph);
        int new_cost = new_perm.calc_lb_full();
        if (new_cost < best_cost)
        {
            best_perm = std::move(new_perm);
            best_cost = new_cost;
        }
    }
    return best_perm;
}
