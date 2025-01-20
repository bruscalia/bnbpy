#ifndef NEH_H
#define NEH_H

#include <vector>
#include <algorithm>

#include "job.hpp"
#include "sigma.hpp"
#include "permutation.hpp"
#include "utils.hpp"


inline bool desc_T(const JobPtr &a, const JobPtr &b);

Permutation neh_constructive(std::vector<JobPtr> &jobs);

#endif  // NEH_H
