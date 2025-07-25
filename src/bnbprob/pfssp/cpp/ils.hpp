#ifndef ILS_HPP
#define ILS_HPP

#include <algorithm>
#include <random>
#include <vector>

#include "intensify.hpp"
#include "job.hpp"
#include "local_search.hpp"
#include "neh.hpp"
#include "permutation.hpp"
#include "sigma.hpp"

struct ILSDestruction
{
    Sigma sigma;
    std::vector<JobPtr> jobs;
};

ILSDestruction ils_destruction(Sigma sigma, int d, int seed);

Permutation ils(std::vector<JobPtr> &jobs, int max_iter);

#endif  // ILS_HPP