#include "permutation.hpp"

#include <algorithm>
#include <memory>
#include <vector>

#include "job.hpp"
#include "sigma.hpp"

int LARGE = 10000000;

// Constructor from processing times
Permutation::Permutation(const Int3D &p_)
    : m(fill_m(p_.at(0))),
      n(p_.size()),
      level(0),
      sigma1(m),
      free_jobs(n),
      sigma2(m)
{
    // Constructor implementation here
    // Create jobs used in permutation solution
    for (int j = 0; j < n; ++j)
    {
        const Int2D &pj = p_[j];
        this->free_jobs[j] = std::make_shared<Job>(j, pj);
    }

    // Update parameters
    update_params();
}

// Accessor methods
JobPtr1D *Permutation::get_free_jobs()
{
    return &free_jobs;
}

Sigma *Permutation::get_sigma1()
{
    return &sigma1;
}

Sigma *Permutation::get_sigma2()
{
    return &sigma2;
}

JobPtr1D Permutation::get_sequence()
{
    // Implementation here
    JobPtr1D seq = {};
    seq.reserve(this->sigma1.jobs.size() + this->free_jobs.size() +
                this->sigma2.jobs.size());
    seq.insert(seq.end(), this->sigma1.jobs.begin(), this->sigma1.jobs.end());
    seq.insert(seq.end(), this->free_jobs.begin(), this->free_jobs.end());
    seq.insert(seq.end(), this->sigma2.jobs.begin(), this->sigma2.jobs.end());
    return seq;
}

JobPtr1D Permutation::get_sequence_copy()
{
    // Implementation here
    JobPtr1D base_seq = get_sequence();
    JobPtr1D seq = copy_jobs(base_seq);
    return seq;
}

Int2D Permutation::get_r()
{
    // Returns a 2D vector: for each semiline, for each machine, the min r among free_jobs
    Int2D r_;
    if (!this->m) return r_;
    int n_semilines = this->m->size();
    r_.resize(n_semilines);
    for (int sl = 0; sl < n_semilines; ++sl)
    {
        int m_sl = (*this->m)[sl];
        r_[sl].resize(m_sl, LARGE);
        for (int k = 0; k < m_sl; ++k)
        {
            int min_r = LARGE;
            for (const auto& job : this->free_jobs)
            {
                if (job->r.size() > sl && job->r[sl].size() > k)
                    min_r = std::min(min_r, job->r[sl][k]);
            }
            r_[sl][k] = min_r;
        }
    }
    return r_;
}

Int2D Permutation::get_q()
{
    // Returns a 2D vector: for each semiline, for each machine, the min q among free_jobs
    Int2D q_;
    if (!this->m) return q_;
    int n_semilines = this->m->size();
    q_.resize(n_semilines);
    for (int sl = 0; sl < n_semilines; ++sl)
    {
        int m_sl = (*this->m)[sl];
        q_[sl].resize(m_sl, LARGE);
        for (int k = 0; k < m_sl; ++k)
        {
            int min_q = LARGE;
            for (const auto& job : this->free_jobs)
            {
                if (job->q.size() > sl && job->q[sl].size() > k)
                    min_q = std::min(min_q, job->q[sl][k]);
            }
            q_[sl][k] = min_q;
        }
    }
    return q_;
}

// Modification methods
void Permutation::push_job(const int &j)
{
    JobPtr &jobptr = this->free_jobs[j];
    // Implementation here
    if (this->level % 2 == 0)
    {
        this->sigma1.job_to_bottom(jobptr);
        this->free_jobs.erase(this->free_jobs.begin() + j);
        this->front_updates();
    }
    else
    {
        this->sigma2.job_to_top(jobptr);
        this->free_jobs.erase(this->free_jobs.begin() + j);
        this->back_updates();
    }
    this->level += 1;
}

void Permutation::update_params()
{
    // Implementation here
    this->front_updates();
    this->back_updates();
}

void Permutation::front_updates()
{
    // For each free job, update r for all semilines and machines
    for (auto& job : this->free_jobs)
    {
        int job_rec = 0;
        for (size_t sl = 0; sl < this->m->size(); ++sl)
        {
            int m_sl = (*this->m)[sl];
            // Update up to the reconciliation machine
            job->r[sl][0] = this->sigma1.C[sl][0];
            int k = 1;
            for (; k < m_sl - job->s; ++k)
            {
                job->r[sl][k] = std::max(
                    this->sigma1.C[sl][k],
                    job->r[sl][k - 1] + job->p->at(sl)[k - 1]
                );
            }
            job_rec = std::max(job_rec, job->r[sl][k - 1] + job->p->at(sl)[k - 1]);
        }
        // Update reconciliation machine(s)
        for (size_t sl = 0; sl < this->m->size(); ++sl)
        {
            int m_sl = (*this->m)[sl];
            int recon_idx = m_sl - job->s;
            job->r[sl][recon_idx] = std::max(this->sigma1.C[sl][recon_idx], job_rec);
            for (int k = recon_idx + 1; k < m_sl; ++k)
            {
                job->r[sl][k] = std::max(
                    this->sigma1.C[sl][k],
                    job->r[sl][k - 1] + job->p->at(sl)[k - 1]
                );
            }
        }
    }
}

void Permutation::back_updates()
{
    // For each free job, update q for all semilines and machines
    for (auto& job : this->free_jobs)
    {
        int job_rec = 0;
        for (size_t sl = 0; sl < this->m->size(); ++sl)
        {
            int m_sl = (*this->m)[sl];
            int m_ = m_sl - 1;
            // Update from the last machine backwards up to the reconciliation machine
            job->q[sl][m_] = this->sigma2.C[sl][m_];
            int k = 1;
            for (; k < job->s; ++k)
            {
                job->q[sl][m_ - k] = std::max(
                    this->sigma2.C[sl][m_ - k],
                    job->q[sl][m_ - k + 1] + job->p->at(sl)[m_ - k + 1]
                );
            }
            job_rec = std::max(job_rec, job->q[sl][m_] + job->p->at(sl)[m_]);
        }
        // Update before reconciliation machine(s)
        for (size_t sl = 0; sl < this->m->size(); ++sl)
        {
            int m_sl = (*this->m)[sl];
            int m_ = m_sl - job->s - 1;
            if (m_ < 0) continue;
            job->q[sl][m_] = std::max(this->sigma2.C[sl][m_], job_rec);
            for (int t = 1; t < m_sl - job->s; ++t)
            {
                --m_;
                if (m_ < 0) break;
                job->q[sl][m_] = std::max(
                    this->sigma2.C[sl][m_],
                    job->q[sl][m_ + 1] + job->p->at(sl)[m_ + 1]
                );
            }
        }
    }
}

void Permutation::compute_starts() {
    JobPtr1D seq = this->get_sequence();
    // Initialize all r to zero
    for (auto& job : seq) {
        for (size_t sl = 0; sl < this->m->size(); ++sl) {
            int m_sl = (*this->m)[sl];
            job->r[sl].assign(m_sl, 0);
        }
    }
    if (seq.empty()) return;
    // First job
    this->compute_start_first_job(seq[0]);
    // Remaining jobs
    for (size_t j = 1; j < seq.size(); ++j) {
        JobPtr& job = seq[j];
        JobPtr& prev = seq[j - 1];
        int job_rec = 0;
        // Update on each semiline
        for (size_t sl = 0; sl < this->m->size(); ++sl) {
            int m_sl = (*this->m)[sl];
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
        for (size_t sl = 0; sl < this->m->size(); ++sl) {
            int m_sl = (*this->m)[sl];
            int recon_idx = m_sl - job->s;
            job_rec = std::max(job_rec, prev->r[sl][recon_idx] + prev->p->at(sl)[recon_idx]);
        }
        for (size_t sl = 0; sl < this->m->size(); ++sl) {
            int m_sl = (*this->m)[sl];
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

int Permutation::calc_lb_full()
{
    // Returns the maximum over all semilines and machines of sigma1.C + sigma2.C
    int cost = 0;
    for (size_t sl = 0; sl < this->m->size(); ++sl)
    {
        int m_sl = (*this->m)[sl];
        for (int k = 0; k < m_sl; ++k)
        {
            int val = this->sigma1.C[sl][k] + this->sigma2.C[sl][k];
            cost = std::max(cost, val);
        }
    }
    return cost;
}

int Permutation::lower_bound_1m()
{
    // For each semiline and machine, compute min r + sum p + min q over free_jobs
    int max_value = 0;
    for (size_t sl = 0; sl < this->m->size(); ++sl)
    {
        int m_sl = (*this->m)[sl];
        for (int k = 0; k < m_sl; ++k)
        {
            int min_r = LARGE;
            int min_q = LARGE;
            int sum_p = 0;
            for (const auto& jobptr : this->free_jobs)
            {
                min_r = std::min(min_r, jobptr->r[sl][k]);
                min_q = std::min(min_q, jobptr->q[sl][k]);
                sum_p += jobptr->p->at(sl)[k];
            }
            int temp_value = min_r + sum_p + min_q;
            max_value = std::max(max_value, temp_value);
        }
    }
    return max_value;
}

int Permutation::lower_bound_2m()
{
    // For each semiline, for each pair of machines, compute the two-machine bound
    int lbs = 0;
    Int2D r = this->get_r();
    Int2D q = this->get_q();

    for (size_t sl = 0; sl < this->m->size(); ++sl)
    {
        int m_sl = (*this->m)[sl];
        for (int m1 = 0; m1 < m_sl - 1; ++m1)
        {
            for (int m2 = m1 + 1; m2 < m_sl; ++m2)
            {
                int temp_value =
                    r[sl][m1] +
                    two_mach_problem(this->free_jobs, sl, m1, m2) +
                    q[sl][m2];
                lbs = std::max(lbs, temp_value);
            }
        }
    }
    return lbs;
}

void Permutation::compute_start_first_job(const JobPtr& job) {
    int job_rec = 0;
    for (size_t sl = 0; sl < this->m->size(); ++sl) {
        int m_sl = (*this->m)[sl];
        // Update the first job on each semiline
        for (int m_ = 1; m_ < m_sl - job->s; ++m_) {
            job->r[sl][m_] = job->r[sl][m_ - 1] + job->p->at(sl)[m_ - 1];
        }
        int m_ = m_sl - job->s - 1;
        if (m_ >= 0)
            job_rec = std::max(job_rec, job->r[sl][m_] + job->p->at(sl)[m_]);
    }
    // Update the first job on the reconciliation machine(s)
    for (size_t sl = 0; sl < this->m->size(); ++sl) {
        int m_sl = (*this->m)[sl];
        int recon_idx = m_sl - job->s;
        job->r[sl][recon_idx] = job_rec;
        for (int m_ = recon_idx + 1; m_ < m_sl; ++m_) {
            job->r[sl][m_] = job->r[sl][m_ - 1] + job->p->at(sl)[m_ - 1];
        }
    }
}

inline bool asc_t1(const JobParams &a, const JobParams &b)
{
    return a.t1 < b.t1;  // Sort by t1 in ascending order
}

inline bool desc_t2(const JobParams &a, const JobParams &b)
{
    return b.t2 < a.t2;  // Sort by t2 in descending order
}

// Two machine problem definition
int two_mach_problem(const JobPtr1D &jobs, const int &sl, const int &m1, const int &m2)
{
    // sl: semiline index, m1, m2: machine indices
    std::vector<JobParams> j1;
    std::vector<JobParams> j2;
    j1.reserve(jobs.size());
    j2.reserve(jobs.size());

    for (const auto &job : jobs)
    {
        int t1 = job->p->at(sl)[m1] + job->lat->at(sl)[m2][m1];
        int t2 = job->p->at(sl)[m2] + job->lat->at(sl)[m2][m1];
        if (t1 <= t2)
        {
            j1.emplace_back(
                t1, t2,
                job->p->at(sl)[m1],
                job->p->at(sl)[m2],
                job->lat->at(sl)[m2][m1]
            );
        }
        else
        {
            j2.emplace_back(
                t1, t2,
                job->p->at(sl)[m1],
                job->p->at(sl)[m2],
                job->lat->at(sl)[m2][m1]
            );
        }
    }

    // Sort set1 in ascending order of t1
    std::sort(j1.begin(), j1.end(), asc_t1);

    // Sort set2 in descending order of t2
    std::sort(j2.begin(), j2.end(), desc_t2);

    // Concatenate j2 after j1
    j1.insert(j1.end(), j2.begin(), j2.end());

    // Compute makespan
    int res = two_mach_makespan(j1);
    return res;
}

// Makespan given ordered operations
int two_mach_makespan(const std::vector<JobParams> &job_times)
{
    int time_m1 = 0;
    int time_m2 = 0;

    for (const auto &jt : job_times)
    {
        time_m1 += *jt.p1;
        time_m2 = std::max(time_m1 + *jt.lat, time_m2) + *jt.p2;
    }

    return std::max(time_m1, time_m2);
}
