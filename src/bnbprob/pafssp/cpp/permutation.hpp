#ifndef PERMUTATION_HPP
#define PERMUTATION_HPP

#include <algorithm>
#include <memory>
#include <unordered_map>
#include <vector>

#include "job.hpp"
#include "mach_graph.hpp"
#include "sigma.hpp"
#include "single_mach.hpp"
#include "two_mach.hpp"

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
    std::shared_ptr<MachineGraph> mach_graph;

    // Default constructor
    Permutation() : m(0), n(0), level(0), scheduled_jobs(), single_mach_cache() {}

    // Constructor from processing times
    Permutation(const std::vector<std::vector<int>> &p_,
                const std::shared_ptr<MachineGraph> &mach_graph_);

    // Constructor from free jobs
    Permutation(const int &m_, const std::vector<JobPtr> &jobs_,
                const std::shared_ptr<MachineGraph> &mach_graph_)
        : m(m_),
          n(jobs_.size()),
          level(0),
          sigma1(m_, mach_graph_),
          free_jobs(jobs_),
          sigma2(m_, mach_graph_),
          mach_graph(mach_graph_),
          two_mach_cache(std::make_shared<TwoMach>(m, free_jobs)),
          scheduled_jobs(n, false),
          single_mach_cache(m_, jobs_)
    {
        // Constructor implementation here
        update_params();
        complete_prescheduled();
    }

    // Constructor given all desired attributes
    Permutation(const int &m_, const int &n_, const int &level_,
                const Sigma &sigma1_, const std::vector<JobPtr> &free_jobs_,
                const Sigma &sigma2_,
                const std::shared_ptr<MachineGraph> &mach_graph_,
                const std::shared_ptr<TwoMach> &two_mach_cache_)
        : m(m_),
          n(n_),
          level(level_),
          sigma1(sigma1_),
          free_jobs(free_jobs_),
          sigma2(sigma2_),
          mach_graph(mach_graph_),
          two_mach_cache(two_mach_cache_),
          scheduled_jobs(n_, false),
          single_mach_cache(m_, free_jobs_)
    {
        // Constructor implementation here
        update_params();
        complete_prescheduled();
    }

    // Constructor given all desired attributes but two_mach
    Permutation(const int &m_, const int &n_, const int &level_,
                const Sigma &sigma1_, const std::vector<JobPtr> &free_jobs_,
                const Sigma &sigma2_,
                const std::shared_ptr<MachineGraph> &mach_graph_)
        : m(m_),
          n(n_),
          level(level_),
          sigma1(sigma1_),
          free_jobs(free_jobs_),
          sigma2(sigma2_),
          mach_graph(mach_graph_),
          two_mach_cache(std::make_shared<TwoMach>(m_, free_jobs_)),
          scheduled_jobs(n_, false),
          single_mach_cache(m_, free_jobs_)
    {
        // Constructor implementation here
        update_params();
        complete_prescheduled();
    }

    // Constructor from processing times with MachineGraph object
    Permutation(const std::vector<std::vector<int>> &p_,
                const MachineGraph &mach_graph_)
        : Permutation(p_, std::make_shared<MachineGraph>(mach_graph_))
    {
    }

    // Constructor from free jobs with MachineGraph object
    Permutation(const int &m_, const std::vector<JobPtr> &jobs_,
                const MachineGraph &mach_graph_)
        : Permutation(m_, jobs_, std::make_shared<MachineGraph>(mach_graph_))
    {
    }

    // Constructor given all desired attributes with MachineGraph object
    Permutation(const int &m_, const int &n_, const int &level_,
                const Sigma &sigma1_, const std::vector<JobPtr> &free_jobs_,
                const Sigma &sigma2_, const MachineGraph &mach_graph_,
                const std::shared_ptr<TwoMach> &two_mach_cache_)
        : Permutation(m_, n_, level_, sigma1_, free_jobs_, sigma2_,
                      std::make_shared<MachineGraph>(mach_graph_),
                      two_mach_cache_)
    {
    }

    // Constructor given all desired attributes but two_mach with MachineGraph
    // object
    Permutation(const int &m_, const int &n_, const int &level_,
                const Sigma &sigma1_, const std::vector<JobPtr> &free_jobs_,
                const Sigma &sigma2_, const MachineGraph &mach_graph_)
        : Permutation(m_, n_, level_, sigma1_, free_jobs_, sigma2_,
                      std::make_shared<MachineGraph>(mach_graph_))
    {
    }

    // Accessor methods
    std::vector<JobPtr> get_free_jobs();
    Sigma get_sigma1();
    Sigma get_sigma2();
    std::vector<JobPtr> get_sequence();
    std::vector<int> get_r() const;
    std::vector<int> get_q() const;
    std::vector<JobTimes *> get_job_times(const int &m1, const int &m2) const;
    MachineGraph get_mach_graph() const { return *this->mach_graph.get(); }

    // Modification methods
    void push_job(const unsigned int &j);
    void update_params();
    // TODO: revise to see if it currently doesn't break the logic
    // when called.
    // Create later a separate attribute for job starts if needed.
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

private:
    // Cache for two-machine sequences
    std::shared_ptr<TwoMach> two_mach_cache;
    std::vector<bool> scheduled_jobs;
    // Cache for single-machine sequences
    SingleMach single_mach_cache;

    // Complete prescheduled
    void complete_prescheduled()
    {
        for (const auto &job : sigma1.jobs)
        {
            this->scheduled_jobs[job->j] = true;
        }
        for (const auto &job : sigma2.jobs)
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

// Makespan given ordered operations
int two_mach_makespan(const std::vector<JobTimes *> &job_times, int rho1,
                      int rho2);

#endif  // PERMUTATION_HPP
