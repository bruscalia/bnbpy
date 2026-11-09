#include "instance_data.hpp"

#include <stdexcept>
#include <utility>
#include <vector>

#include "job.hpp"
#include "mach_graph.hpp"
#include "two_mach.hpp"

InstanceData::InstanceData(const std::vector<std::vector<int>> &p,
                           MachineGraph mach_graph)
    : mach_graph_(std::move(mach_graph)),
      jobs_(build_jobs(p, mach_graph_)),
      job_ptrs_(build_job_ptrs(jobs_)),
      two_mach_(mach_graph_, job_ptrs_)
{
}

std::vector<Job> InstanceData::build_jobs(
    const std::vector<std::vector<int>> &p, const MachineGraph &mach_graph)
{
    const size_t m = static_cast<size_t>(mach_graph.get_M());
    std::vector<Job> jobs;
    jobs.reserve(p.size());
    for (size_t j = 0; j < p.size(); ++j)
    {
        if (p[j].size() != m)
        {
            throw std::invalid_argument(
                "Every row of p must have one processing time per machine");
        }
        jobs.emplace_back(static_cast<int>(j), p[j], mach_graph);
    }
    return jobs;
}

std::vector<JobPtr> InstanceData::build_job_ptrs(const std::vector<Job> &jobs)
{
    std::vector<JobPtr> ptrs;
    ptrs.reserve(jobs.size());
    for (const Job &job : jobs)
    {
        ptrs.push_back(&job);
    }
    return ptrs;
}
