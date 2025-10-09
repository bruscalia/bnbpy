#ifndef INTENSIFY_HPP
#define INTENSIFY_HPP

#include <algorithm>
#include <memory>
#include <vector>

#include "job.hpp"
#include "local_search.hpp"
#include "mach_graph.hpp"
#include "permutation.hpp"
#include "sigma.hpp"
#include "utils.hpp"

inline bool desc_T(const Job &a, const Job &b);

// Constructive step in intensification heuristic
Permutation intensification(const Sigma &sigma1,
                            const std::vector<Job> &jobs_,
                            const Sigma &sigma2,
                            const std::shared_ptr<MachineGraph>& mach_graph);

// Intensification heuristic with constructive and local search
Permutation intensify(const Sigma &sigma1, const std::vector<Job> &jobs_,
                      const Sigma &sigma2,
                      const std::shared_ptr<MachineGraph>& mach_graph);

// Intensification heuristic with constructive and local search
Permutation intensify(const Permutation &perm);

// Intensification heuristic with constructive and local search
Permutation intensify_ref(const Permutation &perm, const Permutation &ref_perm);

#endif  // INTENSIFY_HPP
