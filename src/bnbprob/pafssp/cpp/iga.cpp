#include "iga.hpp"

#include <algorithm>
#include <memory>
#include <random>
#include <vector>

#include "intensify.hpp"
#include "job.hpp"
#include "local_search.hpp"
#include "mach_graph.hpp"
#include "neh.hpp"
#include "permutation.hpp"
#include "sigma.hpp"

IGADestruction iga_destruction(std::vector<JobPtr>& jobs_, int d,
                               std::mt19937 generator)
{
    IGADestruction result;
    std::vector<JobPtr> alloc_jobs = jobs_;
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

    // Set results
    result.sequence = std::move(alloc_jobs);
    result.free_jobs = std::move(free_jobs);

    return result;
}

Permutation iga(std::vector<JobPtr>& jobs_,
                const std::shared_ptr<MachineGraph>& mach_graph,
                const int& max_iter)
{
    // Initialize variables for IGA
    int d = jobs_.size() / 10;  // Destruction size
    return iga(jobs_, mach_graph, max_iter, d, 0);
}

Permutation iga(std::vector<JobPtr>& jobs_,
                const std::shared_ptr<MachineGraph>& mach_graph,
                const int& max_iter, const int& seed)
{
    // Initialize variables for IGA
    int d = jobs_.size() / 10;  // Destruction size

    return iga(jobs_, mach_graph, max_iter, d, seed);
}

Permutation iga(std::vector<JobPtr>& jobs_,
                const std::shared_ptr<MachineGraph>& mach_graph,
                const int& max_iter, const int& d, const int& seed)
{
    // Initial local search
    Permutation perm = local_search(jobs_, mach_graph);

    // Initialize variables for IGA
    Permutation best_perm = perm;
    Permutation ref_perm = perm;
    int best_cost = best_perm.calc_lb_full();
    int ref_cost = best_cost;

    // Generator to randomize the solution
    std::mt19937 generator(seed);
    std::uniform_real_distribution<> dist(0.0, 1.0);

    // IGA
    for (int i = 0; i < max_iter; ++i)
    {
        // Destruction phase
        std::vector<JobPtr> perm_jobs = ref_perm.get_sequence();
        IGADestruction destruction = iga_destruction(perm_jobs, d, generator);

        // Intensification phase
        std::vector<JobPtr> new_sequence =
            neh_body(destruction.sequence, destruction.free_jobs, mach_graph);

        // Local search phase
        Permutation new_perm = local_search(new_sequence, mach_graph);
        int new_cost = new_perm.calc_lb_full();

        if (new_cost < best_cost)
        {
            best_perm = std::move(new_perm);
            best_cost = new_cost;
            ref_perm = best_perm;
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
        else if (std::exp((ref_cost - new_cost) / 0.5) > dist(generator))
        {
            // Accept the new solution with some probability
            ref_perm = std::move(new_perm);
            ref_cost = new_cost;
        }
    }

    return best_perm;
}
