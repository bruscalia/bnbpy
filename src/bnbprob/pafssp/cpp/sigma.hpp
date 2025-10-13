#ifndef SIGMA_HPP
#define SIGMA_HPP

#include <memory>
#include <vector>

#include "job.hpp"
#include "mach_graph.hpp"

using namespace std;

class Sigma
{
public:
    // Attributes
    int m;
    std::vector<int> C;
    const MachineGraph *mach_graph;

private:
    std::vector<JobPtr> jobs;
    std::vector<int> p;

public:
    // Default constructor
    Sigma() : m(0), C(), mach_graph(nullptr), jobs(), p() {}

    // Constructor with empty instance and machine graph
    Sigma(const int &m_, const MachineGraph *mach_graph_)
        : m(m_), C(m_, 0), mach_graph(mach_graph_), jobs(), p(m_, 0)
    {
    }

    // Constructor with empty instance and machine graph
    Sigma(const int &m_, const std::shared_ptr<MachineGraph> &mach_graph_)
        : m(m_), C(m_, 0), mach_graph(mach_graph_.get()), jobs(), p(m_, 0)
    {
    }

    // Constructor with jobs and machine graph (from JobPtr vector)
    Sigma(const int &m_, const std::vector<JobPtr> &jobs_,
          const MachineGraph *mach_graph_)
        : m(m_),
          C(m_, 0),
          mach_graph(mach_graph_),
          jobs(jobs_.begin(), jobs_.end()),
          p(m_, 0)
    {
        for (const auto &job : jobs_)
        {
            for (int k = 0; k < m; ++k)
            {
                p[k] += (*job).p[k];
            }
        }
    }

    // Full constructor (from JobPtr vector)
    Sigma(const int &m_, const std::vector<JobPtr> &jobs_,
          const std::vector<int> &C_, const MachineGraph *mach_graph_)
        : m(m_),
          C(C_),
          mach_graph(mach_graph_),
          jobs(jobs_.begin(), jobs_.end()),
          p(m_, 0)
    {
        for (const auto &job : jobs_)
        {
            for (int k = 0; k < m; ++k)
            {
                p[k] += (*job).p[k];
            }
        }
    }

    // Destructor
    ~Sigma() {}

    // Push job to bottom sequence
    void job_to_bottom(JobPtr job);

    // Push job to top sequence
    void job_to_top(JobPtr job);

    // Push job to bottom sequence
    void job_to_bottom(Job job)
    {
        job_to_bottom(&job);
    }

    // Push job to top sequence
    void job_to_top(Job job)
    {
        job_to_top(&job);
    }

    // Get jobs as JobPtr vector
    inline std::vector<JobPtr> get_jobs() const { return jobs; }

    // Get number of jobs
    inline size_t n_jobs() const { return jobs.size(); }

    // Get total processing time on machine (idle time not considered)
    inline int get_p(int machine_idx) const { return p[machine_idx]; }

    // Get machine graph
    MachineGraph get_mach_graph() const { return *this->mach_graph; }
};

#endif  // SIGMA_HPP