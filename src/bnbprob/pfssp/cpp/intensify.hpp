#ifndef INTENSIFY_HPP
#define INTENSIFY_HPP

#include <algorithm>
#include <vector>

#include "job.hpp"
#include "local_search.hpp"
#include "permutation.hpp"
#include "sigma.hpp"
#include "utils.hpp"

inline bool desc_T(const JobPtr &a, const JobPtr &b);

// Constructive step in intensification heuristic
Permutation intensification(const Sigma &sigma1,
                            const std::vector<JobPtr> &jobs,
                            const Sigma &sigma2);

// Intensification heuristic with constructive and local search
Permutation intensify(const Sigma &sigma1, const std::vector<JobPtr> &jobs,
                      const Sigma &sigma2);

// Intensification heuristic with constructive and local search
Permutation intensify(const Permutation &perm);

#endif  // INTENSIFY_HPP
