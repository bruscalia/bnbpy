#ifndef PERMUTATION_HPP
#define PERMUTATION_HPP

#include <algorithm>
#include <memory>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#include "job.hpp"
#include "sigma.hpp"
#include "two_mach.hpp"

const int LARGE = 1000000000;

class Permutation
{
public:
    // Attributes
    int m;  // Number of machines
    int n;  // Number of jobs
    int level;
    Sigma sigma1;
    std::vector<JobPtr> free_jobs;
    Sigma sigma2;

    // Default constructor
    Permutation() : m(0), n(0), level(0) {}

    // Constructor from processing times
    Permutation(const std::vector<std::vector<int>> &p_);

    // Constructor from free jobs
    Permutation(const int &m_, const std::vector<JobPtr> &jobs_)
        : m(m_),
          n(jobs_.size()),
          level(0),
          sigma1(m_),
          free_jobs(jobs_),
          sigma2(m),
          two_mach_cache(std::make_shared<TwoMach>(m, free_jobs))
    {
        // Constructor implementation here
        update_params();
        complete_prescheduled();
    }

    // Constructor given all desired attributes
    Permutation(const int &m_, const int &n_, const int &level_,
                const Sigma &sigma1_, const std::vector<JobPtr> &free_jobs_,
                const Sigma &sigma2_,
                const std::shared_ptr<TwoMach> &two_mach_cache_)
        : m(m_),
          n(n_),
          level(level_),
          sigma1(sigma1_),
          free_jobs(free_jobs_),
          sigma2(sigma2_),
          two_mach_cache(two_mach_cache_)
    {
        // Constructor implementation here
        update_params();
        complete_prescheduled();
    }

    // Constructor given all desired attributes but two_mach
    Permutation(const int &m_, const int &n_, const int &level_,
                const Sigma &sigma1_, const std::vector<JobPtr> &free_jobs_,
                const Sigma &sigma2_)
        : m(m_),
          n(n_),
          level(level_),
          sigma1(sigma1_),
          free_jobs(free_jobs_),
          sigma2(sigma2_),
          two_mach_cache(std::make_shared<TwoMach>(m_, free_jobs_))
    {
        // Constructor implementation here
        update_params();
        complete_prescheduled();
    }

    // Accessor methods
    std::vector<JobPtr> *get_free_jobs();
    Sigma *get_sigma1();
    Sigma *get_sigma2();
    std::vector<JobPtr> get_sequence() const;
    std::vector<JobPtr> get_sequence_copy() const;
    std::vector<JobPtr> get_free_jobs_copy() const;
    std::vector<int> get_r() const;
    std::vector<int> get_q() const;
    std::vector<JobTimes *> get_job_times(const int &m1, const int &m2) const;

    // Modification methods
    void push_job(const int &j);
    void push_job_forward(const int &j);
    void push_job_backward(const int &j);
    void push_job_dyn(const int &j);
    void update_params();
    void front_updates();
    void back_updates();
    void compute_starts();

    // Feasibility check
    bool is_feasible()
    {
        // Implementation here
        bool valid = (this->free_jobs.size() == 0);
        if (valid)
        {
            this->compute_starts();
        }
        return valid;
    }

    // // Lower bound calculations
    int calc_lb_1m()
    {
        // Implementation here
        if (this->free_jobs.size() == 0)
        {
            return this->calc_lb_full();
        }
        return this->lower_bound_1m();
    }
    int calc_lb_2m()
    {
        // Implementation here
        if (this->free_jobs.size() == 0)
        {
            return this->calc_lb_full();
        }
        return this->lower_bound_2m();
    }
    int calc_lb_full();
    int lower_bound_1m();
    int lower_bound_2m();
    int calc_idle_time()
    {
        // Implementation here
        int idle_time = 0;
        for (int k = 0; k < this->m; ++k)
        {
            idle_time += this->sigma1.C[k] + this->sigma2.C[k];
            for (const auto &job : this->sigma1.jobs)
            {
                idle_time -= job->p->at(k);
            }
            for (const auto &job : this->sigma2.jobs)
            {
                idle_time -= job->p->at(k);
            }
        }
        return idle_time;
    }

    void emplace_from_ref_solution(
        const std::vector<JobPtr> &ref_solution)
    {
        // Sort free jobs according to
        // corresponding order in incumbent solution
        sort_free_jobs_reverse(ref_solution);

        while (!this->free_jobs.empty()) {
            JobPtr job = this->free_jobs.back();
            this->sigma1.job_to_bottom(job);
            this->free_jobs.pop_back();
            front_updates();
        }
    }

    // Deepcopy
    Permutation copy() const
    {
        // std:: vector<JobPtr> new_jobs = copy_jobs(this->free_jobs);
        return Permutation(this->m, this->n, this->level, this->sigma1,
                           copy_jobs(this->free_jobs), this->sigma2,
                           this->two_mach_cache, this->scheduled_jobs);
    }

    // Constructor for copy
    Permutation(int m_, int n_, int level_, const Sigma &sigma1_,
                vector<shared_ptr<Job>> &&free_jobs_, const Sigma &sigma2_,
                const std::shared_ptr<TwoMach> &two_mach_cache_,
                const std::unordered_set<int> &scheduled_jobs_)
        : m(m_),
          n(n_),
          level(level_),
          sigma1(sigma1_),
          free_jobs(std::move(free_jobs_)),
          sigma2(sigma2_),
          two_mach_cache(two_mach_cache_),
          scheduled_jobs(scheduled_jobs_)
    {
    }

private:
    std::shared_ptr<TwoMach> two_mach_cache;
    std::unordered_set<int> scheduled_jobs;

    // Complete prescheduled
    void complete_prescheduled()
    {
        for (const auto &job : sigma1.jobs)
        {
            this->scheduled_jobs.emplace(job->j);
        }
        for (const auto &job : sigma2.jobs)
        {
            this->scheduled_jobs.emplace(job->j);
        }
    }

    void sort_free_jobs_reverse(const std::vector<JobPtr> &ref_solution)
    {
        // Sort free jobs according to
        // corresponding order in incumbent solution
        std::unordered_map<int, int> job_pos;
        for (int i = 0; i < ref_solution.size(); ++i)
        {
            job_pos[ref_solution[i]->j] = i;
        }
        std::sort(this->free_jobs.begin(), this->free_jobs.end(),
                  [&job_pos](const JobPtr &a, const JobPtr &b)
                  { return job_pos[a->j] > job_pos[b->j]; });
    }
};

struct JobParams
{
    int t1;
    int t2;
    const int *p1;
    const int *p2;
    const int *lat;

    // Constructor
    JobParams(const int &t1_, const int &t2_, const int *&p1_, const int *&p2_,
              const int *&lat_)
        : t1(t1_), t2(t2_), p1(p1_), p2(p2_), lat(lat_)
    {
    }

    JobParams(const int &t1_, const int &t2_, const int &p1_, const int &p2_,
              const int &lat_)
        : t1(t1_), t2(t2_), p1(&p1_), p2(&p2_), lat(&lat_)
    {
    }
};

// Makespan given ordered operations
int two_mach_makespan(
    const std::vector<JobTimes *> &job_times,
    int rho1,
    int rho2
);

#endif  // PERMUTATION_HPP
