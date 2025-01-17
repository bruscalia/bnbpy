#include <iostream>
#include <memory>
#include <vector>
#include <algorithm>
#include <cstdlib>

#include <job.hpp>
#include <sigma.hpp>

using namespace std;

// Deafult constructor
Sigma::Sigma()
    : m(0),
      jobs(),
      C()
{
}

// Constructor with empty instance
Sigma::Sigma(int &m_)
    : m(m_),
      jobs(),
      C(m_, 0)
{}

// Constructor only jobs
Sigma::Sigma(int &m_, std::vector<JobPtr> &jobs_)
    : m(m_),
      jobs(jobs_),
      C(m_, 0)
{}

// Full constructor (deepcopy of C)
Sigma::Sigma(int &m_, std::vector<JobPtr> &jobs_, std::vector<int> &C_)
    : m(m_),
      jobs(jobs_),
      C(C_)
{}

// Destructor
Sigma::~Sigma()
{}

// Push job to bottom sequence
void Sigma::job_to_bottom(JobPtr &job)
{
    this->jobs.push_back(job);
    // Update
    this->C[0] = std::max(this->C[0], job->r[0]) + job->p->at(0);
    for (int k = 1; k < this->m; ++k)
    {
        this->C[k] = std::max(this->C[k], this->C[k - 1]) + job->p->at(k);
    }
}

// Push job to top sequence
void Sigma::job_to_top(JobPtr &job)
{
    this->jobs.insert(this->jobs.begin(), job);
    // Update
    int M = this->m - 1;
    if (M == -1)
    {
        return;
    }
    // Update
    this->C[M] = std::max(this->C[M], job->q[M]) + job->p->at(M);
    if (M == 0)
    {
        return;
    }
    // Update
    for (int k = M - 1; k >= 0; --k)
    {
        this->C[k] = std::max(this->C[k], this->C[k + 1]) + job->p->at(k);
    }
}
