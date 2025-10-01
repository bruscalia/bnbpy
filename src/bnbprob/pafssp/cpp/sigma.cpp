#include "sigma.hpp"

#include <algorithm>
#include <memory>
#include <vector>

#include "job.hpp"

using namespace std;

// Push job to bottom sequence
void Sigma::job_to_bottom(const JobPtr &job)
{
    this->jobs.push_back(std::move(job));
    // Update
    for (const int &k : this->mach_graph->get_topo_order()) {
        const std::vector<int> &prev_k = this->mach_graph->get_prec(k);
        int max_prev;
        if (prev_k.size() == 0) {
            max_prev = job->r[k];
        } else {
            max_prev = 0;
        }
        for (const int &pk : prev_k) {
            max_prev = std::max(max_prev, this->C[pk]);
        }
        this->C[k] = std::max(this->C[k], max_prev) + job->p->at(k);
    }
}

// Push job to top sequence
void Sigma::job_to_top(const JobPtr &job)
{
    this->jobs.insert(this->jobs.begin(), std::move(job));
    // Update
    for (const int &k : this->mach_graph->get_rev_topo_order()) {
        const std::vector<int> &succ_k = this->mach_graph->get_succ(k);
        int max_succ;
        if (succ_k.size() == 0) {
            max_succ = job->q[k];
        } else {
            max_succ = 0;
        }
        for (const int &sk : succ_k) {
            max_succ = std::max(max_succ, this->C[sk]);
        }
        this->C[k] = std::max(this->C[k], max_succ) + job->p->at(k);
    }
}

// Deepcopy of self
Sigma Sigma::deepcopy() const {
    Sigma other = Sigma();
    other.m = this->m;
    other.C = this->C;
    other.jobs = copy_jobs(this->jobs);
    other.mach_graph = this->mach_graph;
    return other;
}
