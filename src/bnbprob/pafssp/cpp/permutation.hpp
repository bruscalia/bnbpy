#ifndef PERMUTATION_HPP
#define PERMUTATION_HPP

#include <algorithm>
#include <memory>
#include <unordered_map>
#include <vector>

#include "instance_data.hpp"
#include "job.hpp"
#include "job_times.hpp"
#include "mach_graph.hpp"
#include "sigma.hpp"
#include "single_mach.hpp"
#include "two_mach.hpp"

// Search node: partial sequences sigma1 (front) and sigma2 (back), plus the
// free jobs in between.
//
// `instance` (jobs, machine graph and two-machine cache) is borrowed and
// must outlive the Permutation. Copies are cheap and share the instance.
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
    const InstanceData *instance;

private:
    // One byte per job (not std::vector<bool>): plain loads in the
    // two-machine bound scan instead of bit extraction
    std::vector<char> scheduled_jobs;
    // Cache for single-machine sequences
    SingleMach single_mach_cache;

public:
    // Default constructor (no instance; placeholder only)
    Permutation()
        : m(0),
          n(0),
          level(0),
          instance(nullptr),
          scheduled_jobs(),
          single_mach_cache()
    {
    }

    // Root node: all jobs of the instance are free
    explicit Permutation(const InstanceData *instance_)
        : Permutation(instance_, instance_->get_jobs())
    {
    }

    // Given jobs are free and nothing is scheduled
    Permutation(const InstanceData *instance_,
                const std::vector<JobPtr> &free_jobs_)
        : Permutation(instance_, 0,
                      Sigma(instance_->get_m(), &instance_->get_mach_graph()),
                      free_jobs_,
                      Sigma(instance_->get_m(), &instance_->get_mach_graph()))
    {
    }

    // Constructor given all desired attributes
    Permutation(const InstanceData *instance_, int level_,
                const Sigma &sigma1_, const std::vector<JobPtr> &free_jobs_,
                const Sigma &sigma2_)
        : m(instance_->get_m()),
          n(instance_->get_n()),
          level(level_),
          sigma1(sigma1_),
          free_jobs(free_jobs_),
          sigma2(sigma2_),
          instance(instance_),
          scheduled_jobs(instance_->get_n(), 0),
          single_mach_cache(instance_->get_m(), free_jobs_)
    {
        update_params();
        complete_prescheduled();
    }

    // Accessor methods
    std::vector<JobPtr> get_free_jobs() const;
    Sigma get_sigma1() const;
    Sigma get_sigma2() const;
    std::vector<JobPtr> get_sequence() const;
    std::vector<int> get_r() const;
    std::vector<int> get_q() const;
    const MachineGraph &get_mach_graph() const
    {
        return this->instance->get_mach_graph();
    }
    const InstanceData *get_instance() const { return this->instance; }

    // Modification methods
    void push_job(const unsigned int &j);
    void update_params();

    // Start times aligned with get_sequence() order (sigma1, free jobs in
    // their current order, sigma2); does not mutate jobs
    std::vector<std::vector<int>> compute_starts() const;

    // Feasibility check
    bool is_feasible() const { return this->free_jobs.empty(); }

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

    // Two-machine makespan (Johnson order from the instance cache) of the
    // free jobs on machines m1 -> m2, with heads rho1 and tails rho2
    int two_mach_bound(int m1, int m2, int rho1, int rho2) const;
    int calc_idle_time()
    {
        // Implementation here
        int idle_time = 0;
        for (int k = 0; k < this->m; ++k)
        {
            idle_time += this->sigma1.C[k] + this->sigma2.C[k];
            idle_time -= this->sigma1.get_p(k);
            idle_time -= this->sigma2.get_p(k);
        }
        return idle_time;
    }
    int calc_tot_time()
    {
        // Implementation here
        int idle_time = 0;
        for (int k = 0; k < this->m; ++k)
        {
            idle_time += this->sigma1.C[k] + this->sigma2.C[k];
        }
        return idle_time;
    }

    void emplace_from_ref_solution(const std::vector<JobPtr> &ref_solution)
    {
        // Sort free jobs according to
        // corresponding order in incumbent solution
        sort_free_jobs_reverse(ref_solution);

        while (!this->free_jobs.empty())
        {
            JobPtr job = this->free_jobs.back();
            this->sigma1.job_to_bottom(job);
            this->free_jobs.pop_back();
            update_params();
        }
    }

    // Complete prescheduled
    void complete_prescheduled()
    {
        for (const auto &job : sigma1.get_jobs())
        {
            this->scheduled_jobs[job->j] = true;
        }
        for (const auto &job : sigma2.get_jobs())
        {
            this->scheduled_jobs[job->j] = true;
        }
    }

    void sort_free_jobs_reverse(const std::vector<JobPtr> &ref_solution)
    {
        // Sort free jobs according to
        // corresponding order in incumbent solution
        std::unordered_map<int, int> job_pos;
        for (int i = 0; i < static_cast<int>(ref_solution.size()); ++i)
        {
            job_pos[ref_solution[i]->j] = i;
        }
        std::sort(this->free_jobs.begin(), this->free_jobs.end(),
                  [&job_pos](const JobPtr &a, const JobPtr &b)
                  { return job_pos[a->j] > job_pos[b->j]; });
    }
};

#endif  // PERMUTATION_HPP
