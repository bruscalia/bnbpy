#include "job.hpp"

#include <cstdlib>
#include <memory>
#include <vector>

#include "mach_graph.hpp"

using namespace std;

// Private helper function to initialize with MachineGraph precedence relationships
void Job::initialize(const std::shared_ptr<std::vector<int>> &p_, const MachineGraph &mach_graph)
{
    int m = p_->size();

    // Initialize release dates of the job on each machine
    for (int k : mach_graph.get_topo_order()) {
        const std::vector<int> &prev_k = mach_graph.get_prec(k);
        int max_release = 0;
        for (const int &pk : prev_k) {
            max_release = std::max(max_release, r[pk] + p_->at(pk));
        }
        r[k] = max_release;
    }

    // Initialize wait times of the job on each machine
    for (int k : mach_graph.get_rev_topo_order()) {
        const std::vector<int> &succ_k = mach_graph.get_succ(k);
        int max_wait = 0;
        for (const int &sk : succ_k) {
            max_wait = std::max(max_wait, q[sk] + p_->at(sk));
        }
        q[k] = max_wait;
    }

    // The latency between two operations is the difference between
    // their release dates minus the processing time of the first operation
    // If there is no precedence, the latency is 0
    for (int m1 = 0; m1 < m; ++m1)
    {
        (*lat)[m1] = std::vector<int>(m, 0);
        for (int m2 = 0; m2 < m; ++m2)
        {
            if (r[m1] > r[m2] + p_->at(m2)) {
                (*lat)[m1][m2] = r[m1] - (r[m2] + p_->at(m2));
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
