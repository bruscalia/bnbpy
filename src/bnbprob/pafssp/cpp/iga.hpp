#ifndef IGA_HPP
#define IGA_HPP

#include <algorithm>
#include <memory>
#include <random>
#include <vector>

#include "intensify.hpp"
#include "job.hpp"
#include "local_search.hpp"
#include "mach_graph.hpp"
#include "neh.hpp"
#include "permutation.hpp"
#include "sigma.hpp"

struct IGADestruction
{
    std::vector<JobPtr> sequence;
    std::vector<JobPtr> free_jobs;
};

IGADestruction iga_destruction(std::vector<JobPtr>& jobs_, int d,
                               std::mt19937 generator);

Permutation iga(std::vector<JobPtr>& jobs_,
                const std::shared_ptr<MachineGraph>& mach_graph,
                const int& max_iter);

Permutation iga(std::vector<JobPtr>& jobs_,
                const std::shared_ptr<MachineGraph>& mach_graph,
                const int& max_iter, const int& seed);

Permutation iga(std::vector<JobPtr>& jobs_,
                const std::shared_ptr<MachineGraph>& mach_graph,
                const int& max_iter, const int& d, const int& seed);

#endif  // IGA_HPP