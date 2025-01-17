#include <iostream>
#include <fstream>
#include <vector>
#include <job.hpp>
#include <sigma.hpp>
#include <permutation.hpp>


inline bool desc_T(const JobPtr& a, const JobPtr& b);

Permutation neh_constructive(std::vector<JobPtr> &jobs);
