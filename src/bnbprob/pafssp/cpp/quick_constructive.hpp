#ifndef QUICK_CONSTRUCTIVE_HPP
#define QUICK_CONSTRUCTIVE_HPP

#include <vector>
#include <memory>

#include "instance_data.hpp"
#include "job.hpp"
#include "permutation.hpp"
#include "sigma.hpp"
#include "mach_graph.hpp"

inline bool desc_slope(const JobPtr& a, const JobPtr& b);

Permutation quick_constructive(std::vector<JobPtr>& jobs, const InstanceData& inst);

#endif  // QUICK_CONSTRUCTIVE_HPP
