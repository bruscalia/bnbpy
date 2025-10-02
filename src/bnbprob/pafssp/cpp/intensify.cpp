#include "intensify.hpp"

#include <algorithm>
#include <climits>
#include <iostream>
#include <vector>

#include "job.hpp"
#include "local_search.hpp"
#include "permutation.hpp"
#include "sigma.hpp"
#include "utils.hpp"

inline bool desc_T(const JobPtr &a, const JobPtr &b)
{
    return b->get_T() < a->get_T();
}

Permutation intensification(const Sigma &sigma1,
                            const std::vector<JobPtr> &jobs_,
                            const Sigma &sigma2,
                            const std::shared_ptr<MachineGraph>& mach_graph)
{
    int j, j0, i, best_cost, seq_size, cost_alt, best_pos;
    // Sigma s1, s2, sol, best_sol, s_alt;
    JobPtr job;
    std::vector<JobPtr> vec, base_vec, jobs;
    Sigma s1, s2, sol, best_sol;

    jobs = copy_jobs(jobs_);

    // Find best order of two jobs with longest processing times
    std::sort(jobs.begin(), jobs.end(), desc_T);

    // Initial setup for two jobs
    // TODO: Update Sigma to support initialization from MachineGraph
    sol = sigma1.deepcopy();
    std::cout << "Deepcopy was ok" << std::endl;
    j0 = sigma1.jobs.size();
    base_vec = std::vector<JobPtr>();

    // Find best insert for every other job
    seq_size = base_vec.size();
    for (j = 0; j < static_cast<int>(jobs.size()); ++j)
    {
        // TODO: Update Sigma to support initialization from MachineGraph
        Sigma base_sig = sigma1.deepcopy();
        best_cost = INT_MAX;  // Replace with LARGE_INT constant
        best_pos = 0;
        std::cout << "Looping for j" << j << std::endl;
        for (i = 0; i <= seq_size; ++i)
        {
            std::cout << "Looping for i" << i << std::endl;
            // Insert job in position i
            job = jobs[j];
            vec = copy_jobs(base_vec);
            vec.insert(vec.begin() + i, job);
            std::cout << "Insert i OK" << i << std::endl;
            // TODO: new function to compute r0
            recompute_r0(vec);

            // Recompute release dates only of necessary jobs
            if (i > 0)
            {
                base_sig.job_to_bottom(vec[i - 1]);
            }

            // Here the insertion is performed
            // TODO: Update Sigma to support initialization from MachineGraph
            Sigma s_alt = (base_sig);  // Shallow copy
            s_alt.jobs.reserve(vec.size() + j0);
            for (int k = i; k < static_cast<int>(vec.size()); ++k)
            {
                s_alt.job_to_bottom(vec[k]);
                std::cout << "Job to bottom" << k << std::endl;
            }

            // New cost is the greatest completion time
            cost_alt = get_max_value(s_alt.C, sigma2.C);
            std::cout << "Cost" << cost_alt << std::endl;
            if (cost_alt < best_cost)
            {
                best_cost = cost_alt;
                best_sol = std::move(s_alt);
                best_pos = i;
            }
        }
        seq_size += 1;
        sol = std::move(best_sol);
        base_vec.insert(base_vec.begin() + best_pos, jobs[j]);
        std::cout << "Inserted job" << j << std::endl;
    }
    std::cout << "Going to exit" << std::endl;
    // TODO: return Permutation from sigmas and jobs
    Permutation perm = Permutation(
        sol.m, jobs.size(), jobs.size(), sol,
        std::vector<JobPtr>{}, sigma2.deepcopy(), mach_graph);
    return perm;
}

Permutation intensify(const Sigma &sigma1, const std::vector<JobPtr> &jobs,
                      const Sigma &sigma2,
                      const std::shared_ptr<MachineGraph>& mach_graph)
{
    Permutation best_sol;
    // Initialize
    best_sol = intensification(sigma1, jobs, sigma2, mach_graph);

    // Local search iterations
    std::vector<JobPtr> sequence_copy = best_sol.get_sequence_copy();
    best_sol = local_search(sequence_copy, mach_graph);
    return best_sol;
}

Permutation intensify(const Permutation &perm)
{
    return intensify(perm.sigma1, perm.free_jobs, perm.sigma2, perm.mach_graph);
}

Permutation intensify_ref(const Permutation &perm, const Permutation &ref_perm)
{
    Permutation best_sol = perm.copy();
    // Initialize
    best_sol.emplace_from_ref_solution(ref_perm.get_sequence_copy());
    std::vector<JobPtr> sequence_copy = best_sol.get_sequence_copy();
    best_sol = local_search(sequence_copy, perm.mach_graph);
    return best_sol;
}
