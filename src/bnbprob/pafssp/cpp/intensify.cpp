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

Permutation intensify(const Permutation &perm, const Permutation &ref_perm_)
{
    // Create copies to modify
    Permutation best_sol = perm;
    Permutation ref_perm = ref_perm_;
    // Initialize
    std::vector<JobPtr> jobs = ref_perm.get_sequence();
    best_sol.emplace_from_ref_solution(jobs);
    std::vector<JobPtr> seq = best_sol.get_sequence();
    best_sol = local_search(seq, perm.mach_graph);
    return best_sol;
}
