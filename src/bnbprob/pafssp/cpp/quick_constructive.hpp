#ifndef QUICK_CONSTRUCTIVE_HPP
#define QUICK_CONSTRUCTIVE_HPP

#include <vector>
#include <memory>

#include "job.hpp"
#include "permutation.hpp"
#include "sigma.hpp"
#include "mach_graph.hpp"

inline bool desc_slope(const JobPtr& a, const JobPtr& b);

Permutation quick_constructive(std::vector<JobPtr>& jobs, const std::shared_ptr<MachineGraph>& mach_graph);

#endif  // QUICK_CONSTRUCTIVE_HPP
