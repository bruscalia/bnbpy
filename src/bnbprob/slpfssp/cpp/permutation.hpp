#ifndef PERMUTATION_HPP
#define PERMUTATION_HPP

#include <memory>
#include <vector>

#include "job.hpp"
#include "sigma.hpp"

using JobPtr1D = std::vector<JobPtr>;

class Permutation
{
public:
    // Attributes
    Int1DPtr m;  // Number of machines
    int n;  // Number of jobs
    int level;
    Sigma sigma1;
    JobPtr1D free_jobs;
    Sigma sigma2;

    // Default constructor
    Permutation() : m(nullptr), n(0), level(0) {}

    // Constructor from processing times
    Permutation(const Int3D &p_);

    // Constructor from free jobs
    Permutation(const Int1DPtr &m_, const JobPtr1D &jobs_)
        : m(m_),
          n(jobs_.size()),
          level(0),
          sigma1(m_),
          free_jobs(jobs_),
          sigma2(m_)
    {
        // Constructor implementation here
        update_params();
    }

    // Constructor given all desired attributes
    Permutation(const Int1DPtr &m_, const int &n_, const int &level_,
                const Sigma &sigma1_, const JobPtr1D &free_jobs_,
                const Sigma &sigma2_)
        : m(m_),
          n(n_),
          level(level_),
          sigma1(sigma1_),
          free_jobs(free_jobs_),
          sigma2(sigma2_)
    {
        // Constructor implementation here
        update_params();
    }

    // Accessor methods
    JobPtr1D *get_free_jobs();
    Sigma *get_sigma1();
    Sigma *get_sigma2();
    JobPtr1D get_sequence();
    JobPtr1D get_sequence_copy();
    Int2D get_r();
    Int2D get_q();

    // Modification methods
    void push_job(const int &j);
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

    // Deepcopy
    Permutation copy() const
    {
        // std:: vector<JobPtr> new_jobs = copy_jobs(this->free_jobs);
        return Permutation(this->m, this->n, this->level, this->sigma1,
                           copy_jobs(this->free_jobs), this->sigma2);
    }

    // Constructor for copy
    Permutation(Int1DPtr m_, int n_, int level_, const Sigma &sigma1_,
                JobPtr1D &&free_jobs_, const Sigma &sigma2_)
        : m(m_),
          n(n_),
          level(level_),
          sigma1(sigma1_),
          free_jobs(std::move(free_jobs_)),
          sigma2(sigma2_)
    {
    }

private:
    inline Int1DPtr fill_m(const Int2D &p_) {
        Int1DPtr m_ = std::make_shared<Int1D>(p_.size());
        for (size_t i = 0; i < p_.size(); ++i) {
            (*m_)[i] = p_[i].size();
        }
        return m_;
    }
    void compute_start_first_job(const JobPtr& job);
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

// // Two machine problem definition
int two_mach_problem(const JobPtr1D &jobs, const int &sl, const int &m1,
                     const int &m2);

// Makespan given ordered operations
int two_mach_makespan(const std::vector<JobParams> &job_times);

#endif  // PERMUTATION_HPP
