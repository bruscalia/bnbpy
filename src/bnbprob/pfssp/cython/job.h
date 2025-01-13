#ifndef JOB_H
#define JOB_H

#include <vector>

struct Job {
    // Attributes
    const int j;
    const std::vector<int> p;
    std::vector<int> r;
    std::vector<int> q;
    std::vector<std::vector<int>> lat;
    int slope;
    int T;

    //  Default (empty) constructor
    Job()
        : j(0), p(), r(), q(), lat(), slope(0), T(0) {}

    // Only id and processing times
    Job(const int j_, const std::vector<int> p_)
        : j(j_), p(p_), r(), q(), lat(), slope(0), T(0) {}


    // Constructor
    Job(
        const int j_,
        const std::vector<int> p_,
        std::vector<int> r_,
        std::vector<int> q_,
        std::vector<std::vector<int>> lat_,
        int slope_,
        int T_
    )
        : j(j_), p(p_), r(r_), q(q_), lat(lat_), slope(slope_), T(T_) {}

    // Destructor
    // ~Job() {}
};

#endif // JOB_H
