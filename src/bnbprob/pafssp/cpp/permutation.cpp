#include "permutation.hpp"

#include <algorithm>
#include <climits>
#include <memory>
#include <vector>

#include "job.hpp"
#include "sigma.hpp"
#include "single_mach.hpp"
#include "two_mach.hpp"

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
      scheduled_jobs(p_.size(), false),
      single_mach_cache()
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
    this->single_mach_cache = SingleMach(this->m, this->free_jobs);

    // Update parameters
    update_params();
}

// Accessor methods
std::vector<JobPtr> Permutation::get_free_jobs()
{
    return free_jobs;
}

Sigma Permutation::get_sigma1()
{
    return sigma1;
}

Sigma Permutation::get_sigma2()
{
    return sigma2;
}

std::vector<JobPtr> Permutation::get_sequence()
{
    // Implementation here
    std::vector<JobPtr> seq = {};
    std::vector<JobPtr> sigma1_jobs = this->sigma1.jobs;
    std::vector<JobPtr> sigma2_jobs = this->sigma2.jobs;
    seq.reserve(sigma1_jobs.size() + this->free_jobs.size() +
                sigma2_jobs.size());
    seq.insert(seq.end(), sigma1_jobs.begin(), sigma1_jobs.end());
    seq.insert(seq.end(), this->free_jobs.begin(), this->free_jobs.end());
    seq.insert(seq.end(), sigma2_jobs.begin(), sigma2_jobs.end());
    return seq;
}

std::vector<int> Permutation::get_r() const
{
    // Implementation here
    return this->single_mach_cache.r;
}

std::vector<int> Permutation::get_q() const
{
    // Implementation here
    return this->single_mach_cache.q;
}

std::vector<JobTimes *> Permutation::get_job_times(const int &m1,
                                                   const int &m2) const
{
    std::vector<JobTimes *> seq = {};
    const JobTimes1D &full_seq = this->two_mach_cache->get_seq(m1, m2);
    seq.reserve(full_seq.size());
    for (const JobTimes &jt : full_seq)
    {
        if (!this->scheduled_jobs[jt.job.j])
        {
            seq.push_back(const_cast<JobTimes *>(&jt));
        }
    }
    return seq;
}

// Modification methods
void Permutation::push_job(const unsigned int &j)
{
    JobPtr job = this->free_jobs[j];
    this->scheduled_jobs[job->j] = true;
    this->single_mach_cache.update_p(job);
    // Implementation here
    if (this->level % 2 == 0)
    {
        this->sigma1.job_to_bottom(job);
        // Efficient O(1) removal: swap with last element and pop
        if (j < this->free_jobs.size() - 1)
        {
            std::swap(this->free_jobs[j], this->free_jobs.back());
        }
        this->free_jobs.pop_back();
        this->update_params();
    }
    else
    {
        this->sigma2.job_to_top(job);
        // Efficient O(1) removal: swap with last element and pop
        if (j < this->free_jobs.size() - 1)
        {
            std::swap(this->free_jobs[j], this->free_jobs.back());
        }
        this->free_jobs.pop_back();
        this->update_params();
    }
    this->level += 1;
}

void Permutation::update_params()
{
    // Implementation here
    const size_t free_jobs_size = this->free_jobs.size();
    // Reinitialize single machine cache r and q vectors
    this->single_mach_cache.r = std::vector<int>(this->m, SHRT_MAX);
    this->single_mach_cache.q = std::vector<int>(this->m, SHRT_MAX);
    // Recompute r and q for all free jobs saving information
    // only to single machine cache
    for (size_t j = 0; j < free_jobs_size; ++j)
    {
        JobPtr &job = this->free_jobs[j];
        std::vector<int> &jp = *job->p;
        // Worst-case: copy-on-write if r or q are shared
        std::vector<int> jr = *job->r;
        std::vector<int> jq = *job->q;
        // For r it should go in topological order
        for (const int &k : this->mach_graph->get_topo_order())
        {
            const std::vector<int> &prev_k = this->mach_graph->get_prec(k);
            int max_prev_r = 0;
            for (const int &pk : prev_k)
            {
                max_prev_r = std::max(max_prev_r, jr[pk] + jp[pk]);
            }
            jr[k] = std::max(this->sigma1.C[k], max_prev_r);
            this->single_mach_cache.r[k] =
                std::min(this->single_mach_cache.r[k], jr[k]);
        }
        // For q it should go in reverse topological order
        for (const int &k : this->mach_graph->get_rev_topo_order())
        {
            const std::vector<int> &succ_k = this->mach_graph->get_succ(k);
            int max_succ_q = 0;
            for (const int &sk : succ_k)
            {
                max_succ_q = std::max(max_succ_q, jq[sk] + jp[sk]);
            }
            jq[k] = std::max(this->sigma2.C[k], max_succ_q);
            this->single_mach_cache.q[k] =
                std::min(this->single_mach_cache.q[k], jq[k]);
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
        // Copy-on-write: create new r if it's shared
        if (seq[j]->r.use_count() > 1) {
            seq[j]->r = std::make_shared<std::vector<int>>(*seq[j]->r);
        }
        for (int i = 0; i < this->m; ++i)
        {
            (*seq[j]->r)[i] = 0;  // Set each element to 0
        }
    }

    // Process jobs in sequence order
    for (size_t j = 0; j < seq_size; ++j)
    {
        JobPtr job = seq[j];
        // Cache pointer dereference for efficiency
        const std::vector<int> &jp = *job->p;

        // Process machines in topological order to respect precedence
        for (const int &k : this->mach_graph->get_topo_order())
        {
            int earliest_start = 0;

            // Check predecessor machines for this job
            const std::vector<int> &prev_machines =
                this->mach_graph->get_prec(k);
            for (const int &prev_k : prev_machines)
            {
                earliest_start =
                    std::max(earliest_start, (*job->r)[prev_k] + jp[prev_k]);
            }

            // Check previous jobs on the same machine
            if (j > 0)
            {
                JobPtr prev_job = seq[j - 1];
                // Cache pointer dereference for previous job
                const std::vector<int> &prev_jp = *prev_job->p;
                earliest_start =
                    std::max(earliest_start, (*prev_job->r)[k] + prev_jp[k]);
            }

            (*job->r)[k] = earliest_start;
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
    return this->single_mach_cache.get_bound();
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
        time_m1 += job_times[j]->p1;
        time_m2 =
            std::max(time_m1 + job_times[j]->lat, time_m2) + job_times[j]->p2;
    }
    time_m1 += rho2;

    return std::max(time_m1, time_m2);
}
