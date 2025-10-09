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

inline bool desc_T(const Job &a, const Job &b)
{
    return b.get_T() < a.get_T();
}

Permutation neh_constructive(std::vector<Job> &jobs,
                             const std::shared_ptr<MachineGraph> &mach_graph);

Permutation neh_core(std::vector<Job> &jobs_,
                     const std::shared_ptr<MachineGraph> &mach_graph);

std::vector<Job> neh_body(std::vector<Job> sol_jobs, std::vector<Job> &jobs,
                            const std::shared_ptr<MachineGraph> &mach_graph);

#endif  // NEH_HPP
