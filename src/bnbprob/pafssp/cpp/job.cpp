#include "job.hpp"

#include <climits>
#include <cstdlib>
#include <memory>
#include <vector>

#include "mach_graph.hpp"

using namespace std;

// Private helper function to initialize with MachineGraph precedence
// relationships
void Job::initialize(const std::shared_ptr<std::vector<int>> &p_,
                     const MachineGraph &mach_graph)
{
    int m = p_->size();

    // Recompute release dates (r) and wait times (q)
    recompute_r_q(mach_graph);

    // The latency between two operations is the longest path between them
    // minus the processing time of the first operation
    // Compute longest paths between all pairs of machines
    const std::vector<std::vector<int>> &descendants = mach_graph.get_descendants();

    for (int m1 = 0; m1 < m; ++m1)
    {
        (*lat)[m1] = std::vector<int>(m, 0);

        // Compute longest path from m1 to ALL destinations in a single pass
        // dist[k] = longest path from m1 to k
        std::vector<int> dist(m, INT_MIN);
        dist[m1] = 0;

        // Process machines in topological order
        for (int k : mach_graph.get_topo_order())
        {
            // This is not a descendant of m1
            if (dist[k] == INT_MIN) continue;

            // Update distances to all successors
            for (int succ : mach_graph.get_succ(k))
            {
                dist[succ] = std::max(dist[succ], dist[k] + p_->at(k));
            }
        }

        // Only populate latency for reachable descendants of m1
        for (int m2 : descendants[m1])
        {
            if (dist[m2] != INT_MIN)
            {
                (*lat)[m1][m2] = std::max(0, dist[m2] - p_->at(m1));
            }
            // If not reachable, latency remains 0 (already initialized)
        }
        // Note: (*lat)[m1][m1] remains 0 as initialized, and non-descendants remain 0
    }
}

// Get total time
int Job::get_T() const
{
    int m = p->size();
    int T = 0;
    for (int i = 0; i < m; ++i)
    {
        T += (*p)[i];
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

// Method to recompute only r and q for the job given machine graph
void Job::recompute_r_q(const MachineGraph &mach_graph)
{
    int m = p->size();

    // Create new vectors for r and q (copy-on-write behavior)
    // Only create new shared_ptr if current ones are shared
    if (r.use_count() > 1) {
        r = std::make_shared<std::vector<int>>(m, 0);
    } else {
        r->assign(m, 0);
    }

    if (q.use_count() > 1) {
        q = std::make_shared<std::vector<int>>(m, 0);
    } else {
        q->assign(m, 0);
    }

    // Initialize release dates of the job on each machine
    for (int k : mach_graph.get_topo_order())
    {
        const std::vector<int> &prev_k = mach_graph.get_prec(k);
        int max_release = 0;
        for (const int &pk : prev_k)
        {
            max_release = std::max(max_release, (*r)[pk] + p->at(pk));
        }
        (*r)[k] = max_release;
    }

    // Initialize wait times of the job on each machine
    for (int k : mach_graph.get_rev_topo_order())
    {
        const std::vector<int> &succ_k = mach_graph.get_succ(k);
        int max_wait = 0;
        for (const int &sk : succ_k)
        {
            max_wait = std::max(max_wait, (*q)[sk] + p->at(sk));
        }
        (*q)[k] = max_wait;
    }
}

// Function to copy a vector of jobs with reinitialization from j and p
std::vector<Job> copy_reset(
    const std::vector<Job> &jobs,
    const MachineGraph &mach_graph)
{
    std::vector<Job> out = jobs;
    for (int i = 0; i < static_cast<int>(jobs.size()); ++i)
    {
        // Only recompute r and q (cheap operations)
        out[i].recompute_r_q(mach_graph);
    }
    return out;  // Return the reinitialized vector
}
