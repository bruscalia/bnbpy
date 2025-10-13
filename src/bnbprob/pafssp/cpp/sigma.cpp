#include "sigma.hpp"

#include <algorithm>
#include <memory>
#include <vector>

#include "job.hpp"

using namespace std;

// Push job to bottom sequence
void Sigma::job_to_bottom(Job job)
{
    // Cache pointer dereference for efficiency
    const std::vector<int>& jp = *job.p;

    // Update completion times using the job data
    for (const int &k : this->mach_graph->get_topo_order()) {
        const std::vector<int> &prev_k = this->mach_graph->get_prec(k);
        int max_prev;
        if (prev_k.size() == 0) {
            max_prev = job.r->at(k);
        } else {
            max_prev = 0;
        }
        for (const int &pk : prev_k) {
            max_prev = std::max(max_prev, this->C[pk]);
        }
        this->C[k] = std::max(this->C[k], max_prev) + jp[k];
    }
    // Create shared_ptr and add to jobs vector
    this->jobs.push_back(std::make_shared<Job>(std::move(job)));
}

// Push job to top sequence
void Sigma::job_to_top(Job job)
{
    // Cache pointer dereference for efficiency
    const std::vector<int>& jp = *job.p;

    // Update completion times using the job data
    for (const int &k : this->mach_graph->get_rev_topo_order()) {
        const std::vector<int> &succ_k = this->mach_graph->get_succ(k);
        int max_succ;
        if (succ_k.size() == 0) {
            max_succ = job.q->at(k);
        } else {
            max_succ = 0;
        }
        for (const int &sk : succ_k) {
            max_succ = std::max(max_succ, this->C[sk]);
        }
        this->C[k] = std::max(this->C[k], max_succ) + jp[k];
    }
    // Create shared_ptr and add to jobs vector
    this->jobs.insert(this->jobs.begin(), std::make_shared<Job>(std::move(job)));
}

// Get jobs as raw Job copies
std::vector<Job> Sigma::get_jobs() const
{
    std::vector<Job> result;
    result.reserve(jobs.size());
    for (const auto& job_ptr : jobs) {
        if (job_ptr) {
            result.push_back(*job_ptr);  // Dereference and copy
        }
    }
    return result;
}

// Get raw pointers to jobs for direct modification
std::vector<Job*> Sigma::get_job_ptrs()
{
    std::vector<Job*> result;
    result.reserve(jobs.size());
    for (const auto& job_ptr : jobs) {
        if (job_ptr) {
            result.push_back(job_ptr.get());  // Get raw pointer
        }
    }
    return result;
}

// Deepcopy of self
Sigma Sigma::deepcopy() const {
    Sigma other = Sigma();
    other.m = this->m;
    other.C = this->C;
    other.mach_graph = this->mach_graph;

    // Deep copy jobs by creating new Job objects
    other.jobs.reserve(this->jobs.size());
    for (const auto& job_ptr : this->jobs) {
        if (job_ptr) {
            // Create a new Job object by copying the existing one
            other.jobs.push_back(std::make_shared<Job>(*job_ptr));
        }
    }

    return other;
}
