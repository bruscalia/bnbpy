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
    const MachineGraph* mach_graph;

    // Default constructor
    Sigma() : m(0), jobs(), C(), mach_graph(nullptr) {}

    // Constructor with empty instance and machine graph
    Sigma(const int &m_, const MachineGraph* mach_graph_)
        : m(m_), jobs(), C(m_, 0), mach_graph(mach_graph_) {}

    // Constructor with empty instance and machine graph
    Sigma(const int &m_, const std::shared_ptr<MachineGraph> &mach_graph_)
        : m(m_), jobs(), C(m_, 0), mach_graph(&(*mach_graph_)) {}

    // Constructor with jobs and machine graph
    Sigma(const int &m_, const std::vector<JobPtr> &jobs_, const MachineGraph* mach_graph_)
        : m(m_), jobs(jobs_), C(m_, 0), mach_graph(mach_graph_)
    {
    }

    // Full constructor
    Sigma(const int &m_, const std::vector<JobPtr> &jobs_,
          const std::vector<int> &C_, const MachineGraph* mach_graph_)
        : m(m_), jobs(jobs_), C(C_), mach_graph(mach_graph_)
    {
    }

    // Destructor
    ~Sigma() {}

    // Push job to bottom sequence
    void job_to_bottom(const JobPtr &job);

    // Push job to top sequence
    void job_to_top(const JobPtr &job);

    // Deepcopy of self
    Sigma deepcopy() const;

    // Get machine graph
    MachineGraph get_mach_graph() const
    {
        return *this->mach_graph;
    }

};

#endif  // SIGMA_HPP