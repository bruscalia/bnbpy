#include <iostream>
#include <vector>
#include <limits>

// Recompute release of first machine
void recompute_r0(std::vector<JobPtr> &jobs);

// Get the maximum value of an array of integer by a pointer
int get_max_value(int* ptr, int m);

// The the maximum value of a vector of integers by a pointer
int get_max_value(std::vector<int> &vec);
