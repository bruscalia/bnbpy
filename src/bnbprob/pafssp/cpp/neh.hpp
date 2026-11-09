#ifndef NEH_HPP
#define NEH_HPP

#include <algorithm>
#include <memory>
#include <vector>

#include "instance_data.hpp"
#include "job.hpp"
#include "mach_graph.hpp"
#include "permutation.hpp"
#include "sigma.hpp"
#include "utils.hpp"

inline bool desc_T(const JobPtr &a, const JobPtr &b)
{
    return b->get_T() < a->get_T();
}

Permutation neh_initialization(std::vector<JobPtr> &jobs,
                               const InstanceData &inst);

Permutation neh_core(std::vector<JobPtr> &jobs_, const InstanceData &inst);

std::vector<JobPtr> neh_body(std::vector<JobPtr> sol_jobs,
                             std::vector<JobPtr> &jobs,
                             const MachineGraph &mach_graph);

#endif  // NEH_HPP
