#ifndef LOCAL_SEARCH_HPP
#define LOCAL_SEARCH_HPP

#include <memory>
#include <vector>

#include "job.hpp"
#include "mach_graph.hpp"
#include "permutation.hpp"
#include "sigma.hpp"

struct SearchState
{
    std::vector<JobPtr> jobs;
    int cost;

    // Move constructor from Sigma
    SearchState(std::vector<JobPtr>&& jobs_, int c) : jobs(jobs_), cost(c) {}

    // Copy constructor from Sigma
    SearchState(const std::vector<JobPtr>& jobs_, int c) : jobs(jobs_), cost(c)
    {
    }

    // Default constructor
    SearchState() : jobs(), cost(0) {}
};

SearchState ls_best_move(const std::vector<JobPtr>& jobs_,
                         const std::shared_ptr<MachineGraph>& mach_graph);

Permutation local_search(std::vector<JobPtr>& jobs_,
                         const std::shared_ptr<MachineGraph>& mach_graph);

#endif  // LOCAL_SEARCH_HPP
