#ifndef NEH_HPP
#define NEH_HPP

#include <algorithm>
#include <vector>

#include "job.hpp"
#include "permutation.hpp"
#include "sigma.hpp"
#include "utils.hpp"

inline bool desc_T(const JobPtr &a, const JobPtr &b);

Permutation neh_constructive(std::vector<JobPtr> &jobs);

Permutation neh_core(std::vector<JobPtr> &jobs);

Sigma neh_body(Sigma sol, std::vector<JobPtr> &jobs);

#endif  // NEH_HPP
