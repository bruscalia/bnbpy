#ifndef UTILS_HPP
#define UTILS_HPP

#include <algorithm>
#include <limits>
#include <vector>

#include "job.hpp"

// Recompute release of first machine
void compute_starts_alt(std::vector<JobPtr> &jobs, const Int1D &m);

// Recompute release of first machine
void compute_starts(std::vector<JobPtr> &jobs, const Int1D &m);

// Recompute release of first machine from a given position
void compute_starts(std::vector<JobPtr> &jobs, const Int1D &m, int k);

// Recompute release of first job
void compute_start_first_job(const JobPtr& job, const Int1D& m);

#endif  // UTILS_HPP
