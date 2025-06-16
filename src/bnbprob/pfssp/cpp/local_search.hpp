#ifndef LOCAL_SEARCH_HPP
#define LOCAL_SEARCH_HPP

#include <vector>

#include "job.hpp"
#include "permutation.hpp"

// A new base solution following the same sequence of the current
Permutation local_search(std::vector<JobPtr> &jobs_);

#endif  // LOCAL_SEARCH_HPP
