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
    std::vector<int> p;
    std::vector<int> r;
    std::vector<int> q;
    std::vector<std::vector<int>> lat;
    std::vector<int> s;

    // Default constructor
    Job() : j(0), p(), r(), q(), lat(), s() {}

    // Constructor with job ID, processing times, and
    // MachineGraph
    Job(const int &j_, const std::vector<int> &p_,
        const MachineGraph &mach_graph)
        : j(j_),
          p(p_),
          r(p_.size(), 0),
          q(p_.size(), 0),
          lat(p_.size()),
          s(p_.size(), 0)
    {
        initialize(p_, mach_graph);
    }

    // Parameterized constructor -> shared pointers
    Job(const int &j_, const std::vector<int> &p_, const std::vector<int> &r_,
        const std::vector<int> &q_, const std::vector<std::vector<int>> &lat_,
        const std::vector<int> &s_)
        : j(j_), p(p_), r(r_), q(q_), lat(lat_), s(s_)
    {
    }

    // Destructor
    ~Job() {}

    // Get total time
    int get_T() const;

    // Get slope
    int get_slope() const;

    // Recompute only r and q for the job given machine graph
    void recompute_r_q(const MachineGraph &mach_graph);

private:
    void initialize(const std::vector<int> &p_, const MachineGraph &mach_graph);
};

// Type definition for shared pointer
typedef std::shared_ptr<Job> JobPtr;

#endif  // JOB_HPP
