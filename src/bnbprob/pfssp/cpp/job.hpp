#ifndef JOB_HPP
#define JOB_HPP

#include <memory>
#include <vector>

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
    int slope;
    int T;

    // Default constructor
    Job() : j(0), p(nullptr), r(), q(), lat(nullptr), T(0) {}

    // Constructor with job ID and shared pointer to processing times
    Job(const int &j_, const std::shared_ptr<std::vector<int>> &p_)
        : j(j_),
          p(p_),
          r(p_->size(), 0),
          q(p_->size(), 0),
          lat(std::make_shared<std::vector<std::vector<int>>>(p_->size()))
    {
        initialize(p_);
    }

    // Constructor with job ID and vector for processing times (creates
    // shared_ptr internally)
    Job(const int &j_, const std::vector<int> &p_)
        : j(j_),
          p(std::make_shared<std::vector<int>>(p_)),
          r(p_.size(), 0),
          q(p_.size(), 0),
          lat(std::make_shared<std::vector<std::vector<int>>>(p_.size()))
    {
        initialize(p);
    }

    // Parameterized constructor -> deepcopy of arrays
    Job(const int &j_, const std::shared_ptr<std::vector<int>> &p_,
        const vector<int> &r_, const vector<int> &q_,
        const std::shared_ptr<std::vector<std::vector<int>>> &lat_,
        const int &slope_, const int &T_)
        : j(j_), p(p_), r(r_), q(q_), lat(lat_), slope(slope_), T(T_)
    {
    }

    // Destructor
    ~Job() {}

private:
    void initialize(const std::shared_ptr<std::vector<int>> &p_);
};

// Function to copy a job
inline std::shared_ptr<Job> copy_job(const std::shared_ptr<Job> &jobptr);

// Function to copy a vector of jobs
std::vector<std::shared_ptr<Job>> copy_jobs(
    const std::vector<std::shared_ptr<Job>> &jobs);

// Type definition for shared pointer
typedef std::shared_ptr<Job> JobPtr;

#endif  // JOB_HPP
