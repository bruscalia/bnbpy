#ifndef SIGMA_H
#define SIGMA_H

#include <memory>
#include <vector>
#include <job.hpp>

using namespace std;

class Sigma
{
public:
    // Attributes
    int m;
    std::vector<JobPtr> jobs;
    std::vector<int> C;

    // Deafult constructor
    Sigma();

    // Constructor with empty instance
    Sigma(int& m_);

    // Constructor only jobs
    Sigma(int& m_, std::vector<JobPtr> &jobs_);

    // Full constructor
    Sigma(int& m_, std::vector<JobPtr> &jobs_, std::vector<int> &C_);

    // Destructor
    ~Sigma();

    // Push job to bottom sequence
    void job_to_bottom(JobPtr &job);

    // Push job to top sequence
    void job_to_top(JobPtr &job);
};

#endif // SIGMA_H