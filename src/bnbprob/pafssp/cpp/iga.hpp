#ifndef IGA_HPP
#define IGA_HPP

#include <algorithm>
#include <memory>
#include <random>
#include <vector>

#include "instance_data.hpp"
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

// Removes `d` random jobs (at most all of them) from `jobs_`.
// The generator is advanced, so consecutive calls draw different jobs.
IGADestruction iga_destruction(std::vector<JobPtr>& jobs_, int d,
                               std::mt19937& generator);

// Iterated Greedy Algorithm (Ruiz & Stutzle, 2007) with destruction size
// `d`, which is clamped to the number of jobs.
Permutation iga(std::vector<JobPtr>& jobs_, const InstanceData& inst,
                const int& max_iter, const int& d, const int& seed);

#endif  // IGA_HPP