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

ILSDestruction ils_destruction(Sigma sigma, int d, std::mt19937 generator);

Permutation ils(std::vector<JobPtr> &jobs, const int &max_iter);

Permutation ils(std::vector<JobPtr> &jobs, const int &max_iter, const int &seed);

Permutation ils(std::vector<JobPtr> &jobs, const int &max_iter, const int &d, const int &seed);

Permutation ils(std::vector<JobPtr> &jobs, const int &max_iter, const int &d, const int &max_age,
                const int &seed);

#endif  // ILS_HPP