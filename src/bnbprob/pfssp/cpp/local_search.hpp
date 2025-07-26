#ifndef LOCAL_SEARCH_HPP
#define LOCAL_SEARCH_HPP

#include <vector>

#include "job.hpp"
#include "permutation.hpp"
#include "sigma.hpp"

struct SearchState
{
    Sigma sigma;
    int cost;

    // Move constructor from Sigma
    SearchState(Sigma&& s, int c) : sigma(std::move(s)), cost(c) {}

    // Copy constructor from Sigma
    SearchState(const Sigma& s, int c) : sigma(s), cost(c) {}

    // Default constructor
    SearchState() : sigma(), cost(0) {}
};

SearchState ls_best_move(const std::vector<JobPtr>& jobs);

Permutation local_search(std::vector<JobPtr>& jobs_);

#endif  // LOCAL_SEARCH_HPP
