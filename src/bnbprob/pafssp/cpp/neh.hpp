#ifndef NEH_HPP
#define NEH_HPP

#include <algorithm>
#include <memory>
#include <vector>

#include "job.hpp"
#include "mach_graph.hpp"
#include "permutation.hpp"
#include "sigma.hpp"
#include "utils.hpp"

inline bool desc_T(const JobPtr &a, const JobPtr &b);

Permutation neh_constructive(std::vector<JobPtr> &jobs,
                             const std::shared_ptr<MachineGraph> &mach_graph);

Permutation neh_core(std::vector<JobPtr> &jobs,
                     const std::shared_ptr<MachineGraph> &mach_graph);

Sigma neh_body(Sigma sol, std::vector<JobPtr> &jobs,
               const std::shared_ptr<MachineGraph> &mach_graph);

#endif  // NEH_HPP
