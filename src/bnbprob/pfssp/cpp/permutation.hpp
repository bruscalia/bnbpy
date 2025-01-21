#ifndef PERMUTATION_H
#define PERMUTATION_H

#include <memory>
#include <vector>

#include "job.hpp"
#include "sigma.hpp"

class Permutation {
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
          sigma2(m)
    {
        // Constructor implementation here
        update_params();
    }

    // Constructor given all desired attributes
    Permutation(const int &m_, const int &n_, const int &level_,
                const Sigma &sigma1_, const std::vector<JobPtr> &free_jobs_,
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
    std::vector<JobPtr> *get_free_jobs();
    Sigma *get_sigma1();
    Sigma *get_sigma2();
    std::vector<JobPtr> get_sequence();
    std::vector<JobPtr> get_sequence_copy();
    std::vector<int> get_r();
    std::vector<int> get_q();

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
    int calc_lb_1m() {
        // Implementation here
        if (this->free_jobs.size() == 0) {
            return this->calc_lb_full();
        }
        return this->lower_bound_1m();
    }
    int calc_lb_2m() {
        // Implementation here
        if (this->free_jobs.size() == 0) {
            return this->calc_lb_full();
        }
        return this->lower_bound_2m();
    }
    int calc_lb_full();
    int lower_bound_1m();
    int lower_bound_2m();

    // Deepcopy
    Permutation copy() const {
        // std:: vector<JobPtr> new_jobs = copy_jobs(this->free_jobs);
        return Permutation(
            this->m,
            this->n,
            this->level,
            this->sigma1,
            copy_jobs(this->free_jobs),
            this->sigma2
        );
    }

    // Constructor for copy
    Permutation(
        int m_,
        int n_,
        int level_,
        const Sigma &sigma1_,
        vector<shared_ptr<Job>> &&free_jobs_,
        const Sigma &sigma2_
    )
        : m(m_),
          n(n_),
          level(level_),
          sigma1(sigma1_),
          free_jobs(std::move(free_jobs_)),
          sigma2(sigma2_) {}
};

struct JobParams {
    int t1;
    int t2;
    const int *p1;
    const int *p2;
    const int *lat;

    // Constructor
    JobParams(const int &t1_, const int &t2_, const int *&p1_, const int *&p2_,
              const int *&lat_)
        : t1(t1_), t2(t2_), p1(p1_), p2(p2_), lat(lat_) {}

    JobParams(const int &t1_, const int &t2_, const int &p1_, const int &p2_,
              const int &lat_)
        : t1(t1_), t2(t2_), p1(&p1_), p2(&p2_), lat(&lat_) {}
};

// // Two machine problem definition
int two_mach_problem(const std::vector<JobPtr> &jobs, const int &m1,
                     const int &m2);

// Makespan given ordered operations
int two_mach_makespan(const std::vector<JobParams> &job_times, const int &m1,
                      const int &m2);

#endif  // PERMUTATION_H
