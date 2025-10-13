#ifndef SINGLE_MACH_HPP
#define SINGLE_MACH_HPP

#include <climits>
#include <vector>

#include "job.hpp"

using namespace std;

struct SingleMach
{
    std::vector<int> r;  // Release times for each machine
    std::vector<int> q;  // Tail times for each machine
    std::vector<int> p;  // Processing times for each machine

    // Default constructor - empty cache
    SingleMach() : r(), q(), p() {}

    // Constructor with number of machines - initializes vectors with size m and
    // value 0
    SingleMach(int m) : r(m, SHRT_MAX), q(m, SHRT_MAX), p(m, 0) {}

    // Constructor with all arguments
    SingleMach(const std::vector<int>& r_, const std::vector<int>& q_,
               const std::vector<int>& p_)
        : r(r_), q(q_), p(p_)
    {
    }

    // Constructor from jobs - computes min r, min q, and sum p for each machine
    SingleMach(const int& m, const std::vector<JobPtr>& jobs)
        : r(m, SHRT_MAX), q(m, SHRT_MAX), p(m, 0)
    {
        const size_t jobs_size = jobs.size();
        if (jobs_size == 0)
        {
            r = vector<int>(m, 0);
            q = vector<int>(m, 0);
            p = vector<int>(m, 0);
            return;
        }

        for (int k = 0; k < m; ++k)
        {
            for (const JobPtr& job : jobs)
            {
                if ((*job->r)[k] < r[k])
                {
                    r[k] = (*job->r)[k];
                }
                if ((*job->q)[k] < q[k])
                {
                    q[k] = (*job->q)[k];
                }
                p[k] += job->p->at(k);
            }
        }
    }

    // Get total bound for a specific machine
    int get_bound(int machine) const
    {
        return r[machine] + p[machine] + q[machine];
    }

    // Get maximum bound across all machines
    int get_bound() const
    {
        int max_bound = 0;
        const size_t m = p.size();

        for (size_t k = 0; k < m; ++k)
        {
            max_bound = std::max(max_bound, get_bound(k));
        }

        return max_bound;
    }

    // Update p from deleted job
    void update_p(const JobPtr& job)
    {
        const size_t m = p.size();
        for (size_t k = 0; k < m; ++k)
        {
            p[k] -= job->p->at(k);
        }
    }
};

#endif  // SINGLE_MACH_HPP
