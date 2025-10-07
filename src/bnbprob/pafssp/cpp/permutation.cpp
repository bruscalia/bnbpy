#include "permutation.hpp"

#include <algorithm>
#include <climits>
#include <memory>
#include <vector>

#include "job.hpp"
#include "sigma.hpp"

// Constructor from processing times
Permutation::Permutation(const std::vector<std::vector<int>> &p_,
                         const std::shared_ptr<MachineGraph> &mach_graph_)
    : m(p_[0].size()),
      n(p_.size()),
      level(0),
      sigma1(m, mach_graph_),
      free_jobs(n),
      sigma2(m, mach_graph_),
      mach_graph(mach_graph_),
      scheduled_jobs(p_.size(), false)
{
    // Constructor implementation here
    // Create jobs used in permutation solution
    for (int j = 0; j < n; ++j)
    {
        const std::vector<int> &pj = p_[j];
        this->free_jobs[j] = std::make_shared<Job>(j, pj, *mach_graph_);
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
    std::vector<int> r_(this->m);
    const size_t free_jobs_size = this->free_jobs.size();
    for (int i = 0; i < this->m; ++i)
    {
        short min_rm = SHRT_MAX;
        for (size_t j = 0; j < free_jobs_size; ++j)
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
    std::vector<int> q_(this->m);
    const size_t free_jobs_size = this->free_jobs.size();
    for (int i = 0; i < this->m; ++i)
    {
        short min_qm = SHRT_MAX;
        for (size_t j = 0; j < free_jobs_size; ++j)
        {
            min_qm = std::min(min_qm, this->free_jobs[j]->q[i]);
        }
        q_[i] = min_qm;
    }
    return q_;
}

std::vector<JobTimes *> Permutation::get_job_times(const int &m1,
                                                   const int &m2) const
{
    std::vector<JobTimes *> seq = {};
    const JobTimes1D &full_seq = this->two_mach_cache->get_seq(m1, m2);
    seq.reserve(full_seq.size());
    for (const JobTimes &jt : full_seq)
    {
        if (!this->scheduled_jobs[jt.jobptr->j])
        {
            seq.push_back(const_cast<JobTimes*>(&jt));
        }
    }
    return seq;
}

// Modification methods
void Permutation::push_job(const unsigned int &j)
{
    JobPtr &jobptr = this->free_jobs[j];
    this->scheduled_jobs[jobptr->j] = true;
    // Implementation here
    if (this->level % 2 == 0)
    {
        this->sigma1.job_to_bottom(jobptr);
        // Efficient O(1) removal: swap with last element and pop
        if (j < this->free_jobs.size() - 1)
        {
            std::swap(this->free_jobs[j], this->free_jobs.back());
        }
        this->free_jobs.pop_back();
        this->front_updates();
    }
    else
    {
        this->sigma2.job_to_top(jobptr);
        // Efficient O(1) removal: swap with last element and pop
        if (j < this->free_jobs.size() - 1)
        {
            std::swap(this->free_jobs[j], this->free_jobs.back());
        }
        this->free_jobs.pop_back();
        this->back_updates();
    }
    this->level += 1;
}

void Permutation::push_job_forward(const unsigned int &j)
{
    JobPtr &jobptr = this->free_jobs[j];
    this->scheduled_jobs[jobptr->j] = true;
    this->sigma1.job_to_bottom(jobptr);
    // Efficient O(1) removal: swap with last element and pop
    if (j < this->free_jobs.size() - 1)
    {
        std::swap(this->free_jobs[j], this->free_jobs.back());
    }
    this->free_jobs.pop_back();
    this->front_updates();
    this->level += 1;
}

void Permutation::push_job_backward(const unsigned int &j)
{
    JobPtr &jobptr = this->free_jobs[j];
    this->scheduled_jobs[jobptr->j] = true;
    this->sigma2.job_to_top(jobptr);
    // Efficient O(1) removal: swap with last element and pop
    if (j < this->free_jobs.size() - 1)
    {
        std::swap(this->free_jobs[j], this->free_jobs.back());
    }
    this->free_jobs.pop_back();
    this->back_updates();
    this->level += 1;
}

void Permutation::push_job_dyn(const unsigned int &j)
{
    // Implementation here
    int loss1 = 0;
    int loss2 = 0;
    for (int k = 0; k < this->m; ++k)
    {
        // loss1 = std::max(loss1, this->sigma1.C[k]);
        // loss2 = std::max(loss2, this->sigma2.C[k]);
        loss1 += this->sigma1.C[k];
        loss2 += this->sigma2.C[k];
    }
    if (loss1 < loss2)
    {
        this->push_job_forward(j);
    }
    else if (loss1 > loss2)
    {
        this->push_job_backward(j);
    }
    else
    {
        // If both idle times are equal, default to alternating
        this->push_job(j);
    }
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
    const size_t free_jobs_size = this->free_jobs.size();
    for (size_t j = 0; j < free_jobs_size; ++j)
    {
        Job &job = *this->free_jobs[j];
        std::vector<int> &jp = *job.p;
        for (const int &k : this->mach_graph->get_topo_order())
        {
            const std::vector<int> &prev_k = this->mach_graph->get_prec(k);
            int max_prev = 0;
            for (const int &pk : prev_k)
            {
                max_prev = std::max(max_prev, job.r[pk] + jp[pk]);
            }
            job.r[k] = std::max(this->sigma1.C[k], max_prev);
        }
    }
}

void Permutation::back_updates()
{
    // Implementation here
    const size_t free_jobs_size = this->free_jobs.size();
    for (size_t j = 0; j < free_jobs_size; ++j)
    {
        Job &job = *this->free_jobs[j];
        std::vector<int> &jp = *job.p;
        for (const int &k : this->mach_graph->get_rev_topo_order())
        {
            const std::vector<int> &succ_k = this->mach_graph->get_succ(k);
            int max_succ = 0;
            for (const int &sk : succ_k)
            {
                max_succ = std::max(max_succ, job.q[sk] + jp[sk]);
            }
            job.q[k] = std::max(this->sigma2.C[k], max_succ);
        }
    }
}

void Permutation::compute_starts()
{
    // Implementation here
    std::vector<JobPtr> seq = this->get_sequence();
    const size_t seq_size = seq.size();

    // Initialize all start times to 0
    for (size_t j = 0; j < seq_size; ++j)
    {
        for (int i = 0; i < this->m; ++i)
        {
            seq[j]->r[i] = 0;  // Set each element to 0
        }
    }

    // Process jobs in sequence order
    for (size_t j = 0; j < seq_size; ++j)
    {
        JobPtr &job = seq[j];

        // Process machines in topological order to respect precedence
        for (const int &k : this->mach_graph->get_topo_order())
        {
            int earliest_start = 0;

            // Check predecessor machines for this job
            const std::vector<int> &prev_machines =
                this->mach_graph->get_prec(k);
            for (const int &prev_k : prev_machines)
            {
                earliest_start = std::max(earliest_start,
                                          job->r[prev_k] + job->p->at(prev_k));
            }

            // Check previous jobs on the same machine
            if (j > 0)
            {
                JobPtr &prev_job = seq[j - 1];
                earliest_start = std::max(earliest_start,
                                          prev_job->r[k] + prev_job->p->at(k));
            }

            job->r[k] = earliest_start;
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
    const size_t free_jobs_size = this->free_jobs.size();

    for (int k = 0; k < this->m; ++k)
    {
        int min_r = SHRT_MAX;
        int min_q = SHRT_MAX;
        int sum_p = 0;

        for (size_t j = 0; j < free_jobs_size; ++j)
        {
            Job &jobptr = *this->free_jobs[j];
            if (jobptr.r[k] < min_r)
            {
                min_r = jobptr.r[k];
            }
            if (jobptr.q[k] < min_q)
            {
                min_q = jobptr.q[k];
            }
            sum_p += jobptr.p->at(k);
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
    std::vector<int> r = this->get_r();
    std::vector<int> q = this->get_q();

    for (int m1 = 0; m1 < this->m - 1; ++m1)
    {
        for (const int &m2 : this->mach_graph->get_descendants()[m1])
        {
            int temp_value =
                (r[m1] +
                 two_mach_makespan(get_job_times(m1, m2), (r[m2] - r[m1]),
                                   (q[m1] - q[m2])) +
                 q[m2]);
            lbs = std::max(lbs, temp_value);
        }
    }

    // for (const std::vector<int> &chain : this->mach_graph->get_chains())
    // {
    //     for (size_t idx1 = 0; idx1 < chain.size(); ++idx1)
    //     {
    //         int m1 = chain[idx1];
    //         for (size_t idx2 = idx1 + 1; idx2 < chain.size(); ++idx2)
    //         {
    //             int m2 = chain[idx2];
    //             int temp_value =
    //                 (r[m1] +
    //                  two_mach_makespan(get_job_times(m1, m2), (r[m2] - r[m1]),
    //                                    (q[m1] - q[m2])) +
    //                  q[m2]);
    //             lbs = std::max(lbs, temp_value);
    //         }
    //     }
    // }

    return lbs;
}

// Makespan given ordered operations
int two_mach_makespan(const std::vector<JobTimes *> &job_times, int rho1,
                      int rho2)
{
    // Implementation here
    int time_m1 = 0;
    int time_m2 = rho1;

    const size_t job_times_size = job_times.size();
    for (size_t j = 0; j < job_times_size; ++j)
    {
        time_m1 += *job_times[j]->p1;
        time_m2 =
            std::max(time_m1 + *job_times[j]->lat, time_m2) + *job_times[j]->p2;
    }
    time_m1 += rho2;

    return std::max(time_m1, time_m2);
}
