#ifndef QUICK_CONSTRUCTIVE_H
#define QUICK_CONSTRUCTIVE_H

#include <iostream>
#include <fstream>
#include <vector>

#include "job.hpp"
#include "sigma.hpp"
#include "permutation.hpp"


inline bool desc_slope(const JobPtr& a, const JobPtr& b);

Permutation quick_constructive(std::vector<JobPtr> &jobs);


#endif // QUICK_CONSTRUCTIVE_H
