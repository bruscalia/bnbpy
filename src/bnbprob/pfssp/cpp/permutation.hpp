#ifndef PERMUTATION_H
#define PERMUTATION_H

#include <vector>
#include <memory>
#include <job.hpp>
#include <sigma.hpp>

class Permutation {
public:
    // Attributes
    int m; // Number of machines
    int n; // Number of jobs
    int level;
    Sigma sigma1;
    std::vector<JobPtr> free_jobs;
    Sigma sigma2;

    // Default constructor
    Permutation();

    // Constructor from processing times
    Permutation(std::vector<std::vector<int>>& p_);

    // Constructor from free jobs
    Permutation(int m_, std::vector<JobPtr> &jobs_);

    // Constructor given all desired attributes
    Permutation(
        int m_, int n_, int level_,
        Sigma sigma1_, std::vector<JobPtr> free_jobs_, Sigma sigma2_
    );

    // Accessor methods
    std::vector<JobPtr>& get_free_jobs();
    Sigma* get_sigma1();
    Sigma* get_sigma2();
    std::vector<JobPtr> get_sequence();
    std::vector<JobPtr> get_sequence_copy();
    std::vector<int> get_r();
    std::vector<int> get_q();

    // Modification methods
    void push_job(int& j);
    void update_params();
    void front_updates();
    void back_updates();
    void compute_starts();

    // Feasibility check
    bool is_feasible();

    // // Lower bound calculations
    int calc_lb_1m();
    int calc_lb_2m();
    int calc_lb_full();
    int lower_bound_1m();
    int lower_bound_2m();

    // // Copy methods
    Permutation copy() const;

// private:
//     // Private attributes
//     Sigma sigma1;
//     std::vector<JobPtr> free_jobs;
//     Sigma sigma2;
};

struct JobParams {
    int t1;
    int t2;
    int* p1;
    int* p2;
    int* lat;

    // Constructor
    JobParams(int t1_, int t2_, int* p1_, int* p2_, int* lat_)
        : t1(t1_), t2(t2_), p1(p1_), p2(p2_), lat(lat_) {}

    JobParams(int t1_, int t2_, int &p1_, int &p2_, int &lat_)
        : t1(t1_), t2(t2_), p1(&p1_), p2(&p2_), lat(&lat_) {}
};

// // Two machine problem definition
int two_mach_problem(std::vector<JobPtr>& jobs, int& m1, int& m2);

// Makespan given ordered operations
int two_mach_makespan(
    std::vector<JobParams>& job_times,
    int& m1,
    int& m2
);

#endif // PERMUTATION_H
