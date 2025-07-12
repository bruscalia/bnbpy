#include "twomach.hpp"

#include <algorithm>
#include <map>
#include <memory>
#include <tuple>
#include <vector>

#include "job.hpp"
#include "sigma.hpp"

inline bool asc_t1(const JobParamsPtr& a, const JobParamsPtr& b)
{
    return a->t1 < b->t1;  // Sort by t1 in ascending order
}

inline bool desc_t2(const JobParamsPtr& a, const JobParamsPtr& b)
{
    return b->t2 < a->t2;  // Sort by t2 in descending order
}

// Helper: creates a map from job index (job->j) to JobParamsPtr for a given
// machine pair
JobParamsDict create_jobparams_map(const std::vector<JobPtr>& jobs, int m1,
                                   int m2)
{
    JobParamsDict params_map;
    for (const auto& job : jobs)
    {
        int t1 = job->p->at(m1) + job->lat->at(m2)[m1];
        int t2 = job->p->at(m2) + job->lat->at(m2)[m1];
        JobParamsPtr jp = std::make_shared<JobParams>(
            t1, t2, job->p->at(m1), job->p->at(m2), job->lat->at(m2)[m1]);
        (*params_map)[std::make_tuple(job->j, m1, m2)] = jp;
    }
    return params_map;
}

// Helper: creates the sorted vector for a given machine pair from a map
std::vector<JobParamsPtr> create_sorted_jobparams(
    const JobParamsDict& params_map)
{
    std::vector<JobParamsPtr> j1, j2;
    j1.reserve(params_map->size());
    j2.reserve(params_map->size());

    for (const auto& [idx, jp] : (*params_map))
    {
        if (jp->t1 <= jp->t2)
        {
            j1.push_back(jp);
        }
        else
        {
            j2.push_back(jp);
        }
    }
    // Sort j1 ascending by t1
    std::sort(j1.begin(), j1.end(), asc_t1);
    // Sort j2 descending by t2
    std::sort(j2.begin(), j2.end(), desc_t2);
    // Concatenate
    j1.insert(j1.end(), j2.begin(), j2.end());
    return j1;
}

TwoMach::TwoMach(std::vector<JobPtr> jobs)
{
    if (jobs.empty() || !jobs[0]->p) return;
    int m = jobs[0]->p->size();

    for (int m1 = 0; m1 < m; ++m1)
    {
        for (int m2 = m1 + 1; m2 < m; ++m2)
        {
            auto params_map = create_jobparams_map(jobs, m1, m2);
            // Optionally store params_map in params_map member if needed
            sorted_params[std::make_tuple(m1, m2)] =
                create_sorted_jobparams(params_map);
        }
    }
}

void TwoMach::remove_job(JobPtr jobptr)
{
    if (!params_map) return;

    for (auto& [mach_pair, sorted_vec] : sorted_params)
    {
        int m1 = std::get<0>(mach_pair);
        int m2 = std::get<1>(mach_pair);

        std::tuple<int, int, int> full_key = std::make_tuple(jobptr->j, m1, m2);

        auto it = params_map->find(full_key);
        if (it != params_map->end())
        {
            JobParamsPtr to_remove = it->second;

            // Remove the element from the sorted vector
            sorted_vec.erase(
                std::remove(sorted_vec.begin(), sorted_vec.end(), to_remove),
                sorted_vec.end());

            // Optionally remove from the params_map too
            params_map->erase(it);
        }
    }
}
