#ifndef SIGMA_HPP
#define SIGMA_HPP

#include <memory>
#include <vector>

#include "job.hpp"

using namespace std;

class Sigma
{
public:
    // Attributes
    int m;
    std::vector<JobPtr> jobs;
    std::vector<int> C;

    // Deafult constructor
    Sigma() : m(0), jobs(), C() {}

    // Constructor with empty instance
    Sigma(const int &m_) : m(m_), jobs(), C(m_, 0) {}

    // Constructor only jobs
    Sigma(const int &m_, const std::vector<JobPtr> &jobs_)
        : m(m_), jobs(jobs_), C(m_, 0)
    {
    }

    // Full constructor
    Sigma(const int &m_, const std::vector<JobPtr> &jobs_,
          const std::vector<int> &C_)
        : m(m_), jobs(jobs_), C(C_)
    {
    }

    // Destructor
    ~Sigma() {}

    // Push job to bottom sequence
    void job_to_bottom(const JobPtr &job);

    // Push job to top sequence
    void job_to_top(const JobPtr &job);
};

#endif  // SIGMA_HPP