#ifndef UTILS_H
#define UTILS_H

#include <vector>
#include <algorithm>
#include <limits>

#include "job.hpp"

// Recompute release of first machine
void recompute_r0(std::vector<JobPtr> &jobs);

// Get the maximum value of an array of integer by a pointer
int get_max_value(const int* &ptr, int &m);

// The the maximum value of a vector of integers by a pointer
int get_max_value(const std::vector<int> &vec);


#endif // UTILS_H
