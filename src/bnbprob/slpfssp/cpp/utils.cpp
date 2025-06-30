#include "utils.hpp"

#include <algorithm>
#include <limits>
#include <vector>

#include "job.hpp"

int SMALL = -1000000;

void compute_starts(std::vector<JobPtr> &jobs, const Int1D &m)
{
    compute_starts(jobs, m, 0);
}

void compute_starts(std::vector<JobPtr> &jobs, const Int1D &m, int k)
{
    if (jobs.empty() || k >= static_cast<int>(jobs.size())) return;
    // Only jobs with index >= k are considered
    for (size_t j = k; j < jobs.size(); ++j)
    {
        JobPtr job = jobs[j];
        for (size_t sl = 0; sl < m.size(); ++sl)
        {
            int m_sl = m[sl];
            job->r[sl].assign(m_sl, 0);
        }
    }
    // First job in this range
    JobPtr job = jobs[k];
    for (size_t sl = 0; sl < m.size(); ++sl)
    {
        int m_sl = m[sl];
        for (int m_ = 1; m_ < m_sl; ++m_)
        {
            job->r[sl][m_] = job->r[sl][m_ - 1] + job->p->at(sl)[m_ - 1];
        }
    }
    // Remaining jobs in this range
    for (size_t j = k + 1; j < jobs.size(); ++j)
    {
        JobPtr job = jobs[j];
        JobPtr prev = jobs[j - 1];
        for (size_t sl = 0; sl < m.size(); ++sl)
        {
            int m_sl = m[sl];
            job->r[sl][0] = prev->r[sl][0] + prev->p->at(sl)[0];
            for (int m_ = 1; m_ < m_sl; ++m_)
            {
                job->r[sl][m_] =
                    std::max(job->r[sl][m_ - 1] + job->p->at(sl)[m_ - 1],
                             prev->r[sl][m_] + prev->p->at(sl)[m_]);
            }
        }
    }
}


void compute_starts_alt(std::vector<JobPtr> &jobs, const Int1D &m) {
    // Initialize all r to zero
    for (auto& job : jobs) {
        for (size_t sl = 0; sl < m.size(); ++sl) {
            int m_sl = m[sl];
            job->r[sl].assign(m_sl, 0);
        }
    }
    if (jobs.empty()) return;
    // First job
    compute_start_first_job(jobs[0], m);
    // Remaining jobs
    for (size_t j = 1; j < jobs.size(); ++j) {
        JobPtr& job = jobs[j];
        JobPtr& prev = jobs[j - 1];
        int job_rec = 0;
        // Update on each semiline
        for (size_t sl = 0; sl < m.size(); ++sl) {
            int m_sl = m[sl];
            job->r[sl][0] = prev->r[sl][0] + prev->p->at(sl)[0];
            int m_ = 1;
            for (; m_ < m_sl - job->s; ++m_) {
                job->r[sl][m_] = std::max(
                    job->r[sl][m_ - 1] + job->p->at(sl)[m_ - 1],
                    prev->r[sl][m_] + prev->p->at(sl)[m_]
                );
            }
            if (m_ - 1 >= 0)
                job_rec = std::max(job_rec, job->r[sl][m_ - 1] + job->p->at(sl)[m_ - 1]);
        }
        // Update on reconciliation machine(s)
        for (size_t sl = 0; sl < m.size(); ++sl) {
            int m_sl = m[sl];
            int recon_idx = m_sl - job->s;
            job_rec = std::max(job_rec, prev->r[sl][recon_idx] + prev->p->at(sl)[recon_idx]);
        }
        for (size_t sl = 0; sl < m.size(); ++sl) {
            int m_sl = m[sl];
            int recon_idx = m_sl - job->s;
            job->r[sl][recon_idx] = job_rec;
            for (int m_ = recon_idx + 1; m_ < m_sl; ++m_) {
                job->r[sl][m_] = std::max(
                    job->r[sl][m_ - 1] + job->p->at(sl)[m_ - 1],
                    prev->r[sl][m_] + prev->p->at(sl)[m_]
                );
            }
        }
    }
}


void compute_start_first_job(const JobPtr& job, const Int1D& m) {
    int job_rec = 0;
    for (size_t sl = 0; sl < m.size(); ++sl) {
        int m_sl = m[sl];
        // Update the first job on each semiline
        for (int m_ = 1; m_ < m_sl - job->s; ++m_) {
            job->r[sl][m_] = job->r[sl][m_ - 1] + job->p->at(sl)[m_ - 1];
        }
        int m_ = m_sl - job->s - 1;
        if (m_ >= 0)
            job_rec = std::max(job_rec, job->r[sl][m_] + job->p->at(sl)[m_]);
    }
    // Update the first job on the reconciliation machine(s)
    for (size_t sl = 0; sl < m.size(); ++sl) {
        int m_sl = m[sl];
        int recon_idx = m_sl - job->s;
        job->r[sl][recon_idx] = job_rec;
        for (int m_ = recon_idx + 1; m_ < m_sl; ++m_) {
            job->r[sl][m_] = job->r[sl][m_ - 1] + job->p->at(sl)[m_ - 1];
        }
    }
}
