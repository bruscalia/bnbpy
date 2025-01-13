#ifndef JOB_H
#define JOB_H

#include <vector>
#include <memory>

struct Job {
    // Attributes
    const int j;
    std::shared_ptr<std::vector<int>> p;
    std::vector<int> r;
    std::vector<int> q;
    std::shared_ptr<std::vector<std::vector<int>>> lat;
    int slope;
    int T;

    // Default (empty) constructor
    Job()
        : j(0),
          p(std::make_shared<std::vector<int>>()),
          r(),
          q(),
          lat(std::make_shared<std::vector<std::vector<int>>>()),
          slope(0),
          T(0) {}

    // Constructor with job ID and shared_ptr for processing times
    Job(const int j_, std::shared_ptr<std::vector<int>>& p_)
        : j(j_),
          p(p_),
          r(),
          q(),
          lat(std::make_shared<std::vector<std::vector<int>>>()),
          slope(0),
          T(0) {}

    // Full constructor
    Job(
        const int j_,
        std::shared_ptr<std::vector<int>>& p_,
        std::vector<int> r_,
        std::vector<int> q_,
        std::shared_ptr<std::vector<std::vector<int>>>& lat_,
        int slope_,
        int T_
    )
        : j(j_),
          p(p_),
          r(std::move(r_)),
          q(std::move(q_)),
          lat(lat_),
          slope(slope_),
          T(T_) {}

    // Destructor
    // ~Job() {}
};

#endif // JOB_H
