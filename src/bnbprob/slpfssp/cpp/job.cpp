#include "job.hpp"

#include <algorithm>
#include <memory>
#include <numeric>

// Helper function to fill latency matrix for a semiline
static Int2D fill_lat(const std::vector<int>& p)
{
    size_t m = p.size();
    Int2D lat;
    lat.resize(m, std::vector<int>(m, 0));
    for (size_t m1 = 0; m1 < m; ++m1)
    {
        for (size_t m2 = 0; m2 < m; ++m2)
        {
            if (m2 + 1 < m1)
            {
                int sum_p = 0;
                for (size_t i = m2 + 1; i < m1; ++i)
                {
                    sum_p += p[i];
                }
                lat[m1][m2] = sum_p;
            }
        }
    }
    return lat;
}

// Initialize r, q, and lat based on p
void Job::initialize(const Int2DPtr& p_)
{
    if (!p_) return;
    size_t L = p_->size();
    r.clear();
    q.clear();
    lat->clear();
    r.reserve(L);
    q.reserve(L);
    lat->reserve(L);
    for (size_t l = 0; l < L; ++l)
    {
        size_t m = (*p_)[l].size();
        r.push_back(std::vector<int>(m, 0));
        q.push_back(std::vector<int>(m, 0));
        lat->push_back(fill_lat((*p_)[l]));
    }
}

// Get total processing time (sum over all semilines and machines)
int Job::get_T() const
{
    if (!p) return 0;
    int total = 0;
    for (const auto& semiline : *p)
    {
        total += std::accumulate(semiline.begin(), semiline.end(), 0);
    }
    return total;
}

// Copy a job (shallow copy of p and lat, deep copy of r and q)
std::shared_ptr<Job> copy_job(const std::shared_ptr<Job>& jobptr)
{
    if (!jobptr) return nullptr;
    return std::make_shared<Job>(
        jobptr->j, jobptr->p, jobptr->r, jobptr->q,
        jobptr->lat, jobptr->m, jobptr->s);
}

// Copy a vector of jobs
std::vector<std::shared_ptr<Job>> copy_jobs(
    const std::vector<std::shared_ptr<Job>>& jobs)
{
    std::vector<std::shared_ptr<Job>> out(jobs.size());
    for (int i = 0; i < jobs.size(); ++i)
    {
        out[i] = std::make_shared<Job>(*jobs[i]);
    }
    return out;  // Return the copied vector
}
