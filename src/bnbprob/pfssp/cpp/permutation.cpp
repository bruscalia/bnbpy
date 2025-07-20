#include "permutation.hpp"

#include <algorithm>
#include <memory>
#include <vector>

#include "job.hpp"
#include "sigma.hpp"

int LARGE = 10000000;

// Constructor from processing times
Permutation::Permutation(const std::vector<std::vector<int>> &p_)
    : m(p_[0].size()),
      n(p_.size()),
      level(0),
      sigma1(m),
      free_jobs(n),
      sigma2(m),
      scheduled_jobs()
{
    // Constructor implementation here
    // Create jobs used in permutation solution
    for (int j = 0; j < n; ++j)
    {
        const std::vector<int> &pj = p_[j];
        this->free_jobs[j] = std::make_shared<Job>(j, pj);
    }

    // Creates the cache 2M
    this->two_mach_cache = std::make_shared<TwoMach>(this->m, this->free_jobs);

    // Update parameters
    update_params();
}

// Accessor methods
std::vector<JobPtr> *Permutation::get_free_jobs()
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

std::vector<JobPtr> Permutation::get_sequence() const
{
    // Implementation here
    std::vector<JobPtr> seq = {};
    seq.reserve(this->sigma1.jobs.size() + this->free_jobs.size() +
                this->sigma2.jobs.size());
    seq.insert(seq.end(), this->sigma1.jobs.begin(), this->sigma1.jobs.end());
    seq.insert(seq.end(), this->free_jobs.begin(), this->free_jobs.end());
    seq.insert(seq.end(), this->sigma2.jobs.begin(), this->sigma2.jobs.end());
    return seq;
}

std::vector<JobPtr> Permutation::get_sequence_copy() const
{
    // Implementation here
    std::vector<JobPtr> base_seq = get_sequence();
    std::vector<JobPtr> seq = copy_jobs(base_seq);
    return seq;
}

std::vector<JobPtr> Permutation::get_free_jobs_copy() const
{
    // Implementation here
    std::vector<JobPtr> seq = copy_jobs(this->free_jobs);
    return seq;
}

std::vector<int> Permutation::get_r() const
{
    // Implementation here
    std::vector<int> r_ = std::vector<int>(this->m);
    for (int i = 0; i < this->m; ++i)
    {
        int min_rm = LARGE;
        for (int j = 0; j < this->free_jobs.size(); ++j)
        {
            min_rm = std::min(min_rm, this->free_jobs[j]->r[i]);
        }
        r_[i] = min_rm;
    }
    return r_;
}

std::vector<int> Permutation::get_q() const
{
    // Implementation here
    std::vector<int> q_ = std::vector<int>(this->m);
    for (int i = 0; i < this->m; ++i)
    {
        int min_qm = LARGE;
        for (int j = 0; j < this->free_jobs.size(); ++j)
        {
            min_qm = std::min(min_qm, this->free_jobs[j]->q[i]);
        }
        q_[i] = min_qm;
    }
    return q_;
}

std::vector<JobTimes *> Permutation::get_job_times(
    const int &m1,
    const int &m2
) const
{
    std::vector<JobTimes *> seq = {};
    JobTimes1D &full_seq = this->two_mach_cache->get_seq(m1, m2);
    seq.reserve(full_seq.size());
    for (JobTimes &jt : full_seq)
    {
        if (this->scheduled_jobs.find(jt.jobptr->j) == this->scheduled_jobs.end())
        {
            seq.push_back(&jt);
        }
    }
    return seq;
}

// Modification methods
void Permutation::push_job(const int &j)
{
    JobPtr &jobptr = this->free_jobs[j];
    this->scheduled_jobs.emplace(jobptr->j);
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
    // Implementation here
    for (int j = 0; j < this->free_jobs.size(); ++j)
    {
        JobPtr &job = this->free_jobs[j];
        job->r[0] = this->sigma1.C[0];
        for (int k = 1; k < this->m; ++k)
        {
            job->r[k] =
                std::max(this->sigma1.C[k], job->r[k - 1] + job->p->at(k - 1));
        }
    }
}

void Permutation::back_updates()
{
    // Implementation here
    for (int j = 0; j < this->free_jobs.size(); ++j)
    {
        JobPtr &job = this->free_jobs[j];
        job->q[this->m - 1] = this->sigma2.C[this->m - 1];
        for (int k = this->m - 2; k >= 0; --k)
        {
            job->q[k] =
                std::max(this->sigma2.C[k], job->q[k + 1] + job->p->at(k + 1));
        }
    }
}

void Permutation::compute_starts()
{
    // Implementation here
    std::vector<JobPtr> seq = this->get_sequence();
    for (int j = 0; j < seq.size(); ++j)
    {
        for (int i = 0; i < this->m; ++i)
        {
            seq[j]->r[i] = 0;  // Set each element to 0
        }
    }

    for (int i = 1; i < this->m; ++i)
    {
        seq[0]->r[i] = seq[0]->r[i - 1] + seq[0]->p->at(i - 1);
    }

    for (int j = 1; j < seq.size(); ++j)
    {
        JobPtr &job = seq[j];
        JobPtr &prev = seq[j - 1];
        job->r[0] = prev->r[0] + prev->p->at(0);
        for (int i = 1; i < this->m; ++i)
        {
            job->r[i] = std::max(job->r[i - 1] + job->p->at(i - 1),
                                 prev->r[i] + prev->p->at(i));
        }
    }
}

int Permutation::calc_lb_full()
{
    // Implementation here
    int cost = this->sigma1.C[0] + this->sigma2.C[0];
    for (int k = 1; k < this->m; ++k)
    {
        cost = std::max(cost, this->sigma1.C[k] + this->sigma2.C[k]);
    }
    return cost;
}

int Permutation::lower_bound_1m()
{
    // Implementation here
    int max_value = 0;

    for (int k = 0; k < this->m; ++k)
    {
        int min_r = LARGE;
        int min_q = LARGE;
        int sum_p = 0;

        for (int j = 0; j < this->free_jobs.size(); ++j)
        {
            JobPtr &jobptr = this->free_jobs[j];
            if (jobptr->r[k] < min_r)
            {
                min_r = jobptr->r[k];
            }
            if (jobptr->q[k] < min_q)
            {
                min_q = jobptr->q[k];
            }
            sum_p += jobptr->p->at(k);
        }
        int temp_value = min_r + sum_p + min_q;
        if (temp_value > max_value)
        {
            max_value = temp_value;
        }
    }
    return max_value;
}

int Permutation::lower_bound_2m()
{
    // Implementation here
    int lbs = 0;
    vector<int> r = this->get_r();
    vector<int> q = this->get_q();

    for (int m1 = 0; m1 < this->m; ++m1)
    {
        for (int m2 = m1 + 1; m2 < this->m; ++m2)
        {
            int temp_value =
                (r[m1] +
                 two_mach_makespan(get_job_times(m1, m2)) +
                 q[m2]);
            lbs = std::max(lbs, temp_value);
        }
    }
    return lbs;
}

// Makespan given ordered operations
int two_mach_makespan(const std::vector<JobTimes *> &job_times)
{
    // Implementation here
    int time_m1 = 0;
    int time_m2 = 0;

    for (int j = 0; j < job_times.size(); ++j)
    {
        time_m1 += *job_times[j]->p1;
        time_m2 =
            std::max(time_m1 + *job_times[j]->lat, time_m2) + *job_times[j]->p2;
    }

    return std::max(time_m1, time_m2);
}
