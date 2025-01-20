#include <algorithm>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <vector>

#include "job.hpp"
#include "sigma.hpp"


using namespace std;


// Push job to bottom sequence
void Sigma::job_to_bottom(const JobPtr &job) {
    this->jobs.push_back(job);
    // Update
    this->C[0] = std::max(this->C[0], job->r[0]) + job->p->at(0);
    for (int k = 1; k < this->m; ++k) {
        this->C[k] = std::max(this->C[k], this->C[k - 1]) + job->p->at(k);
    }
}

// Push job to top sequence
void Sigma::job_to_top(const JobPtr &job) {
    this->jobs.insert(this->jobs.begin(), job);
    // Update
    int M = this->m - 1;
    if (M == -1) {
        return;
    }
    // Update
    this->C[M] = std::max(this->C[M], job->q[M]) + job->p->at(M);
    if (M == 0) {
        return;
    }
    // Update
    for (int k = M - 1; k >= 0; --k) {
        this->C[k] = std::max(this->C[k], this->C[k + 1]) + job->p->at(k);
    }
}
