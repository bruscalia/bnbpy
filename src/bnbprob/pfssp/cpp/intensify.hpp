#ifndef INTENSIFY_HPP
#define INTENSIFY_HPP

#include <algorithm>
#include <vector>

#include "job.hpp"
#include "permutation.hpp"
#include "sigma.hpp"
#include "utils.hpp"

inline bool desc_T(const JobPtr &a, const JobPtr &b);

Permutation intensification(const Sigma &sigma1, std::vector<JobPtr> &jobs,
                            const Sigma &sigma2);

#endif  // INTENSIFY_HPP
