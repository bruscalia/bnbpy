#include "sigma.hpp"

#include <algorithm>
#include <memory>
#include <vector>

#include "job.hpp"

using namespace std;

// Push job to bottom sequence
void Sigma::job_to_bottom(JobPtr job)
{
    // Cache pointer dereference for efficiency
    const std::vector<int> &jp = (*job).p;

    // Update completion times using the job data
    for (const int &k : this->mach_graph->get_topo_order())
    {
        const std::vector<int> &prev_k = this->mach_graph->get_prec(k);
        int max_prev;
        if (prev_k.size() == 0)
        {
            max_prev = (*job).r.at(k);
        }
        else
        {
            max_prev = 0;
        }
        for (const int &pk : prev_k)
        {
            max_prev = std::max(max_prev, this->C[pk]);
        }
        this->C[k] = std::max(this->C[k], max_prev) + jp[k];
        this->p[k] += jp[k];
    }
    // Create shared_ptr and add to jobs vector
    this->jobs.push_back(job);
}

// Push job to top sequence
void Sigma::job_to_top(JobPtr job)
{
    // Cache pointer dereference for efficiency
    const std::vector<int> &jp = (*job).p;

    // Update completion times using the job data
    for (const int &k : this->mach_graph->get_rev_topo_order())
    {
        const std::vector<int> &succ_k = this->mach_graph->get_succ(k);
        int max_succ;
        if (succ_k.size() == 0)
        {
            max_succ = (*job).q.at(k);
        }
        else
        {
            max_succ = 0;
        }
        for (const int &sk : succ_k)
        {
            max_succ = std::max(max_succ, this->C[sk]);
        }
        this->C[k] = std::max(this->C[k], max_succ) + jp[k];
        this->p[k] += jp[k];
    }
    // Add job to front of jobs vector (O(N) operation)
    this->jobs.insert(this->jobs.begin(), job);
}
