#ifndef UTILS_HPP
#define UTILS_HPP

#include <algorithm>
#include <limits>
#include <vector>

#include "job.hpp"

// Get the maximum value of an array of integer by a pointer
int get_max_value(const int *&ptr, int &m);

// The the maximum value of a vector of integers by a pointer
int get_max_value(const std::vector<int> &vec);

// Pairwise sum max value for two vectors
int get_max_value(const std::vector<int> &v1, const std::vector<int> &v2);

#endif  // UTILS_HPP
