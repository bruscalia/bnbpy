#ifndef JOB_HPP
#define JOB_HPP

#include <memory>
#include <vector>

#include "mach_graph.hpp"

using namespace std;

class Job
{
public:
    // Attributes
    int j;
    std::shared_ptr<std::vector<int>> p;
    std::vector<int> r;
    std::vector<int> q;
    shared_ptr<vector<vector<int>>> lat;

    // Default constructor
    Job() : j(0), p(nullptr), r(), q(), lat(nullptr) {}

    // Constructor with job ID, shared pointer to processing times, and MachineGraph
    Job(const int &j_, const std::shared_ptr<std::vector<int>> &p_, const MachineGraph &mach_graph)
        : j(j_),
          p(p_),
          r(p_->size(), 0),
          q(p_->size(), 0),
          lat(std::make_shared<std::vector<std::vector<int>>>(p_->size()))
    {
        initialize(p_, mach_graph);
    }

    // Constructor with job ID, vector for processing times, and MachineGraph
    Job(const int &j_, const std::vector<int> &p_, const MachineGraph &mach_graph)
        : j(j_),
          p(std::make_shared<std::vector<int>>(p_)),
          r(p_.size(), 0),
          q(p_.size(), 0),
          lat(std::make_shared<std::vector<std::vector<int>>>(p_.size()))
    {
        initialize(p, mach_graph);
    }

    // Parameterized constructor -> deepcopy of arrays
    Job(const int &j_, const std::shared_ptr<std::vector<int>> &p_,
        const vector<int> &r_, const vector<int> &q_,
        const std::shared_ptr<std::vector<std::vector<int>>> &lat_)
        : j(j_), p(p_), r(r_), q(q_), lat(lat_)
    {
    }

    // Destructor
    ~Job() {}

    // Get total time
    int get_T() const;

    // Get slope
    int get_slope() const;

private:
    void initialize(const std::shared_ptr<std::vector<int>> &p_, const MachineGraph &mach_graph);
};

// Function to copy a job
inline std::shared_ptr<Job> copy_job(const std::shared_ptr<Job> &jobptr);

// Function to copy a vector of jobs
std::vector<std::shared_ptr<Job>> copy_jobs(
    const std::vector<std::shared_ptr<Job>> &jobs);

// Type definition for shared pointer
typedef std::shared_ptr<Job> JobPtr;

#endif  // JOB_HPP
