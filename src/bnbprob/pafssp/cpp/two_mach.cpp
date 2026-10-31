#include "two_mach.hpp"

#include <algorithm>
#include <memory>
#include <vector>

#include "job.hpp"
#include "job_times.hpp"
#include "mach_graph.hpp"

inline bool _asc_t1(const JobTimes &a, const JobTimes &b)
{
    return a.t1 < b.t1;  // Sort by t1 in ascending order
}

inline bool _desc_t2(const JobTimes &a, const JobTimes &b)
{
    return b.t2 < a.t2;  // Sort by t2 in descending order
}

JobTimes1D TwoMach::create_pair_seq(const int &m1, const int &m2,
                                    const std::vector<JobPtr> &jobs)
{
    JobTimes1D j1;
    JobTimes1D j2;
    j1.reserve(jobs.size());
    j2.reserve(jobs.size());

    for (const auto &job : jobs)
    {
        JobTimes jt = JobTimes(m1, m2, *job);
        if (jt.t1 <= jt.t2)
        {
            j1.push_back(jt);
        }
        else
        {
            j2.push_back(jt);
        }
    }

    // Sort set1 in ascending order of t1
    std::sort(j1.begin(), j1.end(), _asc_t1);

    // Sort set2 in descending order of t2
    std::sort(j2.begin(), j2.end(), _desc_t2);

    // Include j2 into j1
    j1.insert(j1.end(), j2.begin(), j2.end());

    return j1;
}

TwoMach::TwoMach(const MachineGraph &mach_graph, const std::vector<JobPtr> &jobs)
    : M(mach_graph.get_M()),
      sorted_seqs(static_cast<size_t>(M) * M),
      is_pair(static_cast<size_t>(M) * M, false)
{
    const auto &descendants = mach_graph.get_descendants();

    for (int m1 = 0; m1 < this->M; ++m1)
    {
        // Use descendants from the graph instead of assuming m2 > m1
        for (int m2 : descendants[m1])
        {
            this->sorted_seqs[m1 * this->M + m2] =
                create_pair_seq(m1, m2, jobs);
            this->is_pair[m1 * this->M + m2] = true;
        }
    }
}
