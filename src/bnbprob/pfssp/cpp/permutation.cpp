#include <algorithm>
#include <memory>
#include <vector>

#include "job.hpp"
#include "sigma.hpp"
#include "permutation.hpp"

int LARGE = 10000000;

// Constructor from processing times
Permutation::Permutation(const std::vector<std::vector<int>> &p_)
    : m(p_[0].size()), n(p_.size()), level(0)
{
    // Constructor implementation here

    // Initialize free_jobs as an empty vector of JobPtr
    this->free_jobs = std::vector<JobPtr>();
    this->free_jobs.reserve(n);

    // Create jobs used in permutation solution
    for (int j = 0; j < n; ++j)
    {
        const std::vector<int> &pj = p_[j];
        this->free_jobs.push_back(std::make_shared<Job>(j, pj));
    }

    // Assign parameters
    this->sigma1 = Sigma(m);
    this->sigma2 = Sigma(m);

    // Update parameters
    update_params();
}

// Accessor methods
std::vector<JobPtr> *Permutation::get_free_jobs() { return &free_jobs; }

Sigma *Permutation::get_sigma1() { return &sigma1; }

Sigma *Permutation::get_sigma2() { return &sigma2; }

std::vector<JobPtr> Permutation::get_sequence()
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

std::vector<JobPtr> Permutation::get_sequence_copy()
{
    // Implementation here
    std::vector<JobPtr> base_seq = get_sequence();
    std::vector<JobPtr> seq = copy_jobs(base_seq);
    return seq;
}

std::vector<int> Permutation::get_r()
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

std::vector<int> Permutation::get_q()
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
            seq[j]->r[i] = 0; // Set each element to 0
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
                (r[m1] + two_mach_problem(this->free_jobs, m1, m2) + q[m2]);
            lbs = std::max(lbs, temp_value);
        }
    }
    return lbs;
}

inline bool asc_t1(const JobParams &a, const JobParams &b)
{
    return a.t1 < b.t1; // Sort by t1 in ascending order
}

inline bool desc_t2(const JobParams &a, const JobParams &b)
{
    return b.t2 < a.t2; // Sort by t2 in descending order
}

// Two machine problem definition
int two_mach_problem(
    const std::vector<JobPtr> &jobs,
    const int &m1,
    const int &m2)
{
    // Implementation here
    int J = jobs.size();

    std::vector<JobParams> j1 = {};
    std::vector<JobParams> j2 = {};

    for (int j = 0; j < jobs.size(); ++j)
    {
        int t1 = jobs[j]->p->at(m1) + jobs[j]->lat->at(m2)[m1];
        int t2 = jobs[j]->p->at(m2) + jobs[j]->lat->at(m2)[m1];
        JobParams jparam =
            JobParams(t1, t2, jobs[j]->p->at(m1), jobs[j]->p->at(m2),
                      jobs[j]->lat->at(m2)[m1]);
        if (t1 <= t2)
        {
            j1.push_back(jparam);
        }
        else
        {
            j2.push_back(jparam);
        }
    }

    // Sort set1 in ascending order of t1
    sort(j1.begin(), j1.end(), asc_t1);

    // Sort set2 in descending order of t2
    sort(j2.begin(), j2.end(), desc_t2);

    // Include j2 into j1
    j1.insert(j1.end(), j2.begin(), j2.end());

    // Concatenate the sorted lists
    int res = two_mach_makespan(j1, m1, m2);
    return res;
}

// Makespan given ordered operations
int two_mach_makespan(
    const std::vector<JobParams> &job_times,
    const int &m1,
    const int &m2)
{
    // Implementation here
    int time_m1 = 0;
    int time_m2 = 0;

    for (int j = 0; j < job_times.size(); ++j)
    {
        time_m1 += *job_times[j].p1;
        time_m2 =
            std::max(time_m1 + *job_times[j].lat, time_m2) + *job_times[j].p2;
    }

    return std::max(time_m1, time_m2);
}
