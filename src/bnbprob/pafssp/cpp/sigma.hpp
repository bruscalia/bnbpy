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
    std::vector<JobPtr> jobs;
    std::vector<int> C;
    const MachineGraph *mach_graph;

    // Default constructor
    Sigma() : m(0), jobs(), C(), mach_graph(nullptr) {}

    // Constructor with empty instance and machine graph
    Sigma(const int &m_, const MachineGraph *mach_graph_)
        : m(m_), jobs(), C(m_, 0), mach_graph(mach_graph_)
    {
    }

    // Constructor with empty instance and machine graph
    Sigma(const int &m_, const std::shared_ptr<MachineGraph> &mach_graph_)
        : m(m_), jobs(), C(m_, 0), mach_graph(&(*mach_graph_))
    {
    }

    // Constructor with jobs and machine graph (from raw Job vector)
    Sigma(const int &m_, const std::vector<Job> &jobs_,
          const MachineGraph *mach_graph_)
        : m(m_), jobs(), C(m_, 0), mach_graph(mach_graph_)
    {
        // Convert raw Jobs to shared_ptr<Job>
        for (const auto &job : jobs_)
        {
            jobs.push_back(std::make_shared<Job>(job));
        }
    }

    // Constructor with jobs and machine graph (from JobPtr vector)
    Sigma(const int &m_, const std::vector<JobPtr> &jobs_,
          const MachineGraph *mach_graph_)
        : m(m_), jobs(jobs_), C(m_, 0), mach_graph(mach_graph_)
    {
    }

    // Full constructor (from raw Job vector)
    Sigma(const int &m_, const std::vector<Job> &jobs_,
          const std::vector<int> &C_, const MachineGraph *mach_graph_)
        : m(m_), jobs(), C(C_), mach_graph(mach_graph_)
    {
        // Convert raw Jobs to shared_ptr<Job>
        for (const auto &job : jobs_)
        {
            jobs.push_back(std::make_shared<Job>(job));
        }
    }

    // Full constructor (from JobPtr vector)
    Sigma(const int &m_, const std::vector<JobPtr> &jobs_,
          const std::vector<int> &C_, const MachineGraph *mach_graph_)
        : m(m_), jobs(jobs_), C(C_), mach_graph(mach_graph_)
    {
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
        // Create shared_ptr and call original method
        std::shared_ptr<Job> job_ptr = std::make_shared<Job>(job);
        job_to_bottom(job_ptr);
    }

    // Push job to top sequence
    void job_to_top(Job job)
    {
        // Create shared_ptr and call original method
        std::shared_ptr<Job> job_ptr = std::make_shared<Job>(job);
        job_to_top(job_ptr);
    }

    // Get machine graph
    MachineGraph get_mach_graph() const { return *this->mach_graph; }
};

#endif  // SIGMA_HPP