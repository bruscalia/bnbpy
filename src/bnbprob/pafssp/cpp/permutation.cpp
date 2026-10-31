#include "permutation.hpp"

#include <algorithm>
#include <climits>
#include <memory>
#include <vector>

#include "instance_data.hpp"
#include "job.hpp"
#include "sigma.hpp"
#include "single_mach.hpp"
#include "two_mach.hpp"

// Accessor methods
std::vector<JobPtr> Permutation::get_free_jobs() const
{
    return free_jobs;
}

Sigma Permutation::get_sigma1() const
{
    return sigma1;
}

Sigma Permutation::get_sigma2() const
{
    return sigma2;
}

std::vector<JobPtr> Permutation::get_sequence() const
{
    // Implementation here
    std::vector<JobPtr> seq = {};
    std::vector<JobPtr> sigma1_jobs = this->sigma1.get_jobs();
    std::vector<JobPtr> sigma2_jobs = this->sigma2.get_jobs();
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
    if (free_jobs_size == 0)
    {
        return;
    }
    const MachineGraph &mach_graph = this->get_mach_graph();
    // Recompute r and q for all free jobs saving information
    // only to single machine cache
    for (size_t j = 0; j < free_jobs_size; ++j)
    {
        const JobPtr job = this->free_jobs[j];
        const std::vector<int> &jp = (*job).p;
        // Local copies: jobs are shared and never mutated
        std::vector<int> jr = (*job).r;
        std::vector<int> jq = (*job).q;
        // For r it should go in topological order
        for (const int &k : mach_graph.get_topo_order())
        {
            const std::vector<int> &prev_k = mach_graph.get_prec(k);
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
        for (const int &k : mach_graph.get_rev_topo_order())
        {
            const std::vector<int> &succ_k = mach_graph.get_succ(k);
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

std::vector<std::vector<int>> Permutation::compute_starts() const
{
    const std::vector<JobPtr> seq = this->get_sequence();
    const size_t seq_size = seq.size();
    // starts[pos][k]: start of the job at position pos on machine k
    std::vector<std::vector<int>> starts(seq_size,
                                         std::vector<int>(this->m, 0));
    if (seq_size == 0)
    {
        return starts;
    }
    const MachineGraph &mach_graph = this->get_mach_graph();

    // Process jobs in sequence order
    for (size_t pos = 0; pos < seq_size; ++pos)
    {
        const std::vector<int> &jp = (*seq[pos]).p;
        std::vector<int> &job_starts = starts[pos];

        // Process machines in topological order to respect precedence
        for (const int &k : mach_graph.get_topo_order())
        {
            int earliest_start = 0;

            // Check predecessor machines for this job
            for (const int &prev_k : mach_graph.get_prec(k))
            {
                earliest_start =
                    std::max(earliest_start, job_starts[prev_k] + jp[prev_k]);
            }

            // Check previous job on the same machine
            if (pos > 0)
            {
                const std::vector<int> &prev_jp = (*seq[pos - 1]).p;
                earliest_start = std::max(earliest_start,
                                          starts[pos - 1][k] + prev_jp[k]);
            }

            job_starts[k] = earliest_start;
        }
    }
    return starts;
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
    int cost = 0;
    for (int k = 0; k < this->m; ++k)
    {
        int r_k = std::max(this->single_mach_cache.r[k], this->sigma1.C[k]);
        int q_k = std::max(this->single_mach_cache.q[k], this->sigma2.C[k]);
        cost = std::max(cost, r_k + q_k + this->single_mach_cache.p[k]);
    }
    return cost;
}

int Permutation::lower_bound_2m()
{
    int lbs = 0;
    const std::vector<int> &r = this->single_mach_cache.r;
    const std::vector<int> &q = this->single_mach_cache.q;

    for (int m1 = 0; m1 < this->m; ++m1)
    {
        for (const int &m2 : this->get_mach_graph().get_descendants()[m1])
        {
            int r_k1 = std::max(r[m1], this->sigma1.C[m1]);
            int r_k2 = std::max(r[m2], this->sigma1.C[m2]);
            int q_k1 = std::max(q[m1], this->sigma2.C[m1]);
            int q_k2 = std::max(q[m2], this->sigma2.C[m2]);
            int temp_value =
                (r_k1 + two_mach_bound(m1, m2, (r_k2 - r_k1), (q_k1 - q_k2)) +
                 q_k2);
            lbs = std::max(lbs, temp_value);
        }
    }

    return lbs;
}

int Permutation::two_mach_bound(int m1, int m2, int rho1, int rho2) const
{
    int time_m1 = 0;
    int time_m2 = rho1;

    // Scan the cached sequence, skipping scheduled jobs (no allocation)
    for (const JobTimes &jt : this->instance->get_two_mach().get_seq(m1, m2))
    {
        if (this->scheduled_jobs[jt.j])
        {
            continue;
        }
        time_m1 += jt.p1;
        time_m2 = std::max(time_m1 + jt.lat, time_m2) + jt.p2;
    }
    time_m1 += rho2;

    return std::max(time_m1, time_m2);
}
