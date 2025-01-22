#include "job.hpp"

#include <cstdlib>
#include <memory>
#include <vector>

using namespace std;

// Private helper function to initialize common operations
void Job::initialize(const std::shared_ptr<std::vector<int>> &p_)
{
    int m = p_->size();

    // Initialize lat matrix and calculate T
    for (int m1 = 0; m1 < m; ++m1)
    {
        (*lat)[m1] = std::vector<int>(m, 0);
        for (int m2 = 0; m2 < m; ++m2)
        {
            if (m2 + 1 < m1)
            {  // Ensure range is valid
                int sum_p = 0;
                for (int i = m2 + 1; i < m1; ++i)
                {
                    sum_p += (*p_)[i];
                }
                (*lat)[m1][m2] = sum_p;
            }
        }
    }
}

// Get total time
int Job::get_T() const
{
    int m = p->size();
    int T = 0;
    for (int i = 0; i < m; ++i)
    {
        T += r[i] + (*p)[i] + q[i];
    }
    return T;
}

// Get slope
int Job::get_slope() const
{
    int slope = 0;
    int m = this->p->size() + 1;
    for (int k = 1; k < m; ++k)
    {
        slope += (k - (m + 1) / 2) * (*this->p)[k - 1];
    }
    return slope;
}

// Function to copy a job
inline std::shared_ptr<Job> copy_job(const std::shared_ptr<Job> &jobptr)
{
    return std::make_shared<Job>(*jobptr);
}

// Function to copy a vector of jobs
std::vector<std::shared_ptr<Job>> copy_jobs(
    const std::vector<std::shared_ptr<Job>> &jobs)
{
    std::vector<std::shared_ptr<Job>> out(jobs.size());
    for (int i = 0; i < jobs.size(); ++i)
    {
        out[i] = make_shared<Job>(*jobs[i]);
    }
    return out;  // Return the copied vector
}
