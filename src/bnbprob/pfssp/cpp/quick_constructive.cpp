#include <iostream>
#include <fstream>
#include <vector>
#include <algorithm>
#include <job.hpp>
#include <sigma.hpp>
#include <permutation.hpp>


inline bool desc_slope(const JobPtr& a, const JobPtr& b){
    return b->slope < a->slope;
}

Permutation quick_constructive(std::vector<JobPtr> &jobs){
    int M = jobs.size();
    std::sort(jobs.begin(), jobs.end(), desc_slope);
    Permutation sol = Permutation(M, jobs);
    for (int i = 0; i < sol.free_jobs.size(); ++i){
        sol.sigma1.job_to_bottom(sol.free_jobs.at(i));
        sol.front_updates();
    }
    return sol;
}
