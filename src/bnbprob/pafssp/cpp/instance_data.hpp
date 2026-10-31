#ifndef INSTANCE_DATA_HPP
#define INSTANCE_DATA_HPP

#include <vector>

#include "job.hpp"
#include "mach_graph.hpp"
#include "two_mach.hpp"

// Immutable data of a flow-shop instance: machine graph, jobs and the
// two-machine (LB5) cache.
//
// Every Permutation/Sigma built from it holds raw pointers into it, so it
// must outlive all of them. It is non-copyable and non-movable so that
// those pointers stay valid; allocate it on the heap.
class InstanceData
{
private:
    // Declaration order matters: jobs_ need mach_graph_,
    // two_mach_ needs job_ptrs_
    MachineGraph mach_graph_;
    std::vector<Job> jobs_;         // never resized after construction
    std::vector<JobPtr> job_ptrs_;  // stable pointers into jobs_
    TwoMach two_mach_;

    static std::vector<Job> build_jobs(const std::vector<std::vector<int>> &p,
                                       const MachineGraph &mach_graph);

    static std::vector<JobPtr> build_job_ptrs(const std::vector<Job> &jobs);

public:
    // Throws std::invalid_argument if a row of p does not have one
    // processing time per machine of the graph
    InstanceData(const std::vector<std::vector<int>> &p,
                 MachineGraph mach_graph);

    InstanceData(const InstanceData &) = delete;
    InstanceData &operator=(const InstanceData &) = delete;
    InstanceData(InstanceData &&) = delete;
    InstanceData &operator=(InstanceData &&) = delete;

    int get_n() const { return static_cast<int>(jobs_.size()); }
    int get_m() const { return mach_graph_.get_M(); }
    const MachineGraph &get_mach_graph() const { return mach_graph_; }
    const std::vector<JobPtr> &get_jobs() const { return job_ptrs_; }
    const TwoMach &get_two_mach() const { return two_mach_; }
};

#endif  // INSTANCE_DATA_HPP
