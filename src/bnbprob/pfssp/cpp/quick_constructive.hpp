#ifndef QUICK_CONSTRUCTIVE_HPP
#define QUICK_CONSTRUCTIVE_HPP

#include <vector>

#include "job.hpp"
#include "permutation.hpp"
#include "sigma.hpp"

inline bool desc_slope(const JobPtr& a, const JobPtr& b);

Permutation quick_constructive(std::vector<JobPtr>& jobs);

#endif  // QUICK_CONSTRUCTIVE_HPP
