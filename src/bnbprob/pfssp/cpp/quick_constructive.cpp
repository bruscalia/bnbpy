#include "quick_constructive.hpp"

#include <algorithm>
#include <vector>

#include "job.hpp"
#include "permutation.hpp"
#include "sigma.hpp"

inline bool desc_slope(const JobPtr& a, const JobPtr& b)
{
    return b->get_slope() < a->get_slope();
}

Permutation quick_constructive(std::vector<JobPtr>& jobs)
{
    int M = jobs[0]->p->size();
    std::sort(jobs.begin(), jobs.end(), desc_slope);
    Permutation sol = Permutation(M, jobs);
    for (int i = 0; i < sol.free_jobs.size(); ++i)
    {
        sol.sigma1.job_to_bottom(sol.free_jobs.at(i));
    }
    sol.free_jobs = {};
    return sol;
}
