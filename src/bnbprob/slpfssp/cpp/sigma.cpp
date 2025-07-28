#include "sigma.hpp"
#include <algorithm>
#include <limits>
#include <memory>
#include <stdexcept>


// Cost: maximum completion time on all machines
int Sigma::cost() const {
    int max_c = 0;
    for (const auto& c : C) {
        for (int ci : c) {
            if (ci > max_c) max_c = ci;
        }
    }
    return max_c;
}

// Insert job at the end (bottom) of the sequence
void Sigma::job_to_bottom(const JobPtr& job) {
    jobs.push_back(job);
    int c_sl = 0; // The earliest release on the reconciliation machine
    Int2D& p_ = *job->p; // Processing times

    // Update on each semiline until reconciliation machine
    for (size_t sl = 0; sl < C.size(); ++sl) {
        auto& c = C[sl];
        int msl = m->at(sl);
        // Defensive: check sizes
        if (c.empty() || job->r.size() <= sl || p_.size() <= sl) continue;

        c[0] = std::max(c[0], job->r[sl][0]) + p_[sl][0];
        for (int k = 1; k < msl - job->s; ++k) {
            c[k] = std::max(c[k], c[k - 1]) + p_[sl][k];
        }
        c_sl = std::max(c[msl - job->s - 1], c_sl);
    }

    // Update on reconciliation machine
    for (size_t sl = 0; sl < C.size(); ++sl) {
        auto& c = C[sl];
        int msl = m->at(sl);
        if (c.empty() || job->r.size() <= sl || p_.size() <= sl) continue;

        int recon_idx = msl - job->s;
        c[recon_idx] = std::max(c_sl, job->r[sl][recon_idx]) + p_[sl][recon_idx];
        for (int k = recon_idx + 1; k < msl; ++k) {
            c[k] = std::max(c[k], c[k - 1]) + p_[sl][k];
        }
    }
}

// Insert job at the beginning (top) of the sequence
void Sigma::job_to_top(const JobPtr& job) {
    jobs.insert(jobs.begin(), job);
    int c_sl = 0; // The earliest wait time on the reconciliation machine
    Int2D& p_ = *job->p; // Processing times

    // Update on each semiline on reconciliation machines (backwards)
    for (size_t sl = 0; sl < C.size(); ++sl) {
        auto& c = C[sl];
        int msl = m->at(sl);
        if (c.empty() || job->q.size() <= sl || p_.size() <= sl) continue;

        int idx = msl - 1;
        if (idx < 0) continue;
        c[idx] = std::max(c[idx], job->q[sl][idx]) + p_[sl][idx];
        for (int s = 1; s < job->s; ++s) {
            --idx;
            if (idx < 0) break;
            c[idx] = std::max(c[idx], c[idx + 1]) + p_[sl][idx];
        }
        c_sl = std::max(c[idx], c_sl);
    }

    // Update on parallel semilines (backwards)
    for (size_t sl = 0; sl < C.size(); ++sl) {
        auto& c = C[sl];
        int msl = m->at(sl);
        if (c.empty() || job->q.size() <= sl || p_.size() <= sl) continue;

        int idx = msl - job->s - 1;
        if (idx < 0) continue;
        c[idx] = std::max(c_sl, job->q[sl][idx]) + p_[sl][idx];
        for (int s = 1; s < msl - job->s; ++s) {
            --idx;
            if (idx < 0) break;
            c[idx] = std::max(c[idx], c[idx + 1]) + p_[sl][idx];
        }
    }
}

// Deepcopy of self
Sigma Sigma::deepcopy() const {
    Sigma other = Sigma();
    other.m = this->m;
    other.C = this->C;
    other.jobs = copy_jobs(this->jobs);
    return other;
}
