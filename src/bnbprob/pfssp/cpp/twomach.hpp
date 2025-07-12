#ifndef TWOMACH_HPP
#define TWOMACH_HPP

#include <map>
#include <memory>
#include <tuple>
#include <vector>

#include "job.hpp"
#include "sigma.hpp"

struct JobParams
{
    int t1;
    int t2;
    const int *p1;
    const int *p2;
    const int *lat;

    // Constructor
    JobParams(const int &t1_, const int &t2_, const int *&p1_, const int *&p2_,
              const int *&lat_)
        : t1(t1_), t2(t2_), p1(p1_), p2(p2_), lat(lat_)
    {
    }

    JobParams(const int &t1_, const int &t2_, const int &p1_, const int &p2_,
              const int &lat_)
        : t1(t1_), t2(t2_), p1(&p1_), p2(&p2_), lat(&lat_)
    {
    }
};

// Type alias for map
using PairKey = std::tuple<int, int>;
using JobParamsPtr = std::shared_ptr<JobParams>;
using JobParamsPtr1D = std::vector<JobParamsPtr>;
using SortedParams = std::map<PairKey, JobParamsPtr1D>;
using JobParamsDict = std::shared_ptr<std::map<std::tuple<int, int, int>, JobParamsPtr>>;

class TwoMach
{
private:
    JobParamsDict params_map;
    SortedParams sorted_params;

public:
    // Default initializer
    TwoMach() : params_map(), sorted_params() {};

    // Initialize from jobs
    TwoMach(std::vector<JobPtr> jobs);

    // Remove one job from all maps in sorted params
    void remove_job(JobPtr jobptr);
};

#endif  // TWOMACH_HPP
