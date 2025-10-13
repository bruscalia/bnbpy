#include "two_mach.hpp"

#include <algorithm>
#include <map>
#include <memory>
#include <tuple>
#include <vector>

#include "job.hpp"
#include "job_times.hpp"

inline bool _asc_t1(const JobTimes &a, const JobTimes &b)
{
    return a.t1 < b.t1;  // Sort by t1 in ascending order
}

inline bool _desc_t2(const JobTimes &a, const JobTimes &b)
{
    return b.t2 < a.t2;  // Sort by t2 in descending order
}

// Define this at file scope (or in an anonymous namespace if in the cpp file)
struct JobTimesPredicate
{
    const Job *target;

    JobTimesPredicate(const Job &jobptr) : target(&jobptr) {}

    bool operator()(const JobTimes &jt) const
    {
        return jt.job.j == target->j;
    }
};

JobTimes1D TwoMach::create_pair_seq(const int &m1, const int &m2,
                                    const std::vector<JobPtr> &jobs)
{
    JobTimes1D j1;
    JobTimes1D j2;
    j1.reserve(jobs.size());
    j2.reserve(jobs.size());

    for (const auto &job : jobs)
    {
        int &lat = job->lat.at(m1)[m2];
        int t1 = job->p.at(m1) + lat;
        int t2 = job->p.at(m2) + lat;
        JobTimes jt = JobTimes(m1, m2, *job);
        if (t1 <= t2)
        {
            j1.push_back(jt);
        }
        else
        {
            j2.push_back(jt);
        }
    }

    // Sort set1 in ascending order of t1
    sort(j1.begin(), j1.end(), _asc_t1);

    // Sort set2 in descending order of t2
    sort(j2.begin(), j2.end(), _desc_t2);

    // Include j2 into j1
    j1.insert(j1.end(), j2.begin(), j2.end());

    return j1;
}

TwoMach::TwoMach(const int &m, const std::vector<JobPtr> &jobs)
{
    for (int m1 = 0; m1 < m; ++m1)
    {
        for (int m2 = m1 + 1; m2 < m; ++m2)
        {
            this->sorted_maps[std::make_tuple(m1, m2)] =
                create_pair_seq(m1, m2, jobs);
        }
    }
}
