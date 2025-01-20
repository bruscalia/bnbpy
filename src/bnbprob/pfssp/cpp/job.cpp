#include <memory>
#include <vector>
#include <cstdlib>

#include "job.hpp"

using namespace std;

// Constructor with shared_ptr to vector
Job::Job()
    : j(0),
      p(nullptr),
      r(),
      q(),
      lat(nullptr),
      T(0)
{
}

// Constructor with shared_ptr to vector
Job::Job(const int &j_, const std::shared_ptr<std::vector<int>> &p_)
    : j(j_),
      p(p_),
      r(p_->size(), 0),
      q(p_->size(), 0),
      lat(std::make_shared<std::vector<std::vector<int>>>(p_->size()))
{
    initialize(p_);
}

// Constructor with vector (creates shared_ptr internally)
Job::Job(const int &j_, const std::vector<int> &p_)
    : j(j_),
      p(std::make_shared<std::vector<int>>(p_)),
      r(p_.size(), 0),
      q(p_.size(), 0),
      lat(std::make_shared<std::vector<std::vector<int>>>(p_.size()))
{
    initialize(p);
}

Job::Job(
    const int &j_,
    const std::shared_ptr<std::vector<int>> &p_,
    const vector<int> &r_,
    const vector<int> &q_,
    const std::shared_ptr<std::vector<std::vector<int>>> &lat_,
    const int &slope_,
    const int &T_)
    : j(j_), p(p_), r(r_), q(q_), lat(lat_), slope(slope_), T(T_)
{}

// Destructor
Job::~Job()
{}

// Private helper function to initialize common operations
void Job::initialize(const std::shared_ptr<std::vector<int>> &p_)
{
    int m = p_->size();
    T = 0;

    // Initialize lat matrix and calculate T
    for (int m1 = 0; m1 < m; ++m1)
    {
        (*lat)[m1] = std::vector<int>(m, 0);
        T += (*p_)[m1];
        for (int m2 = 0; m2 < m; ++m2)
        {
            if (m2 + 1 < m1)
            { // Ensure range is valid
                int sum_p = 0;
                for (int i = m2 + 1; i < m1; ++i)
                {
                    sum_p += (*p_)[i];
                }
                (*lat)[m1][m2] = sum_p;
            }
        }
    }

    // Calculate slope
    slope = 0;
    m += 1;
    for (int k = 1; k < m; ++k)
    {
        slope += (k - (m + 1) / 2) * (*p_)[k - 1];
    }
}

// Function to copy a job
inline std::shared_ptr<Job> copy_job(const std::shared_ptr<Job> &jobptr)
{
    return std::make_shared<Job>(
        jobptr->j,
        jobptr->p,
        jobptr->r,
        jobptr->q,
        jobptr->lat,
        jobptr->slope,
        jobptr->T
    );
}

// Function to copy a vector of jobs
std::vector<std::shared_ptr<Job>> copy_jobs(
    const std::vector<std::shared_ptr<Job>> &jobs)
{
    std::vector<std::shared_ptr<Job>> out;
    out.reserve(jobs.size()); // Reserve space for better performance
    for (int i = 0; i < jobs.size(); ++i)
    {
        out.push_back(copy_job(jobs[i]));
    }
    return out; // Return the copied vector
}
