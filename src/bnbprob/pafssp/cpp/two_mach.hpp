#ifndef TWO_MACH_HPP
#define TWO_MACH_HPP

#include <map>
#include <memory>
#include <tuple>
#include <vector>

#include "job.hpp"
#include "job_times.hpp"

using JobTimes1D = std::vector<JobTimes>;
using MachTuple = std::tuple<int, int>;
using JobTimesMap = std::map<MachTuple, JobTimes1D>;

class TwoMach
{
private:
    JobTimesMap sorted_maps;
    JobTimes1D create_pair_seq(const int &m1, const int &m2,
                               const std::vector<JobPtr> &jobs);

public:
    TwoMach() {}
    TwoMach(const int &m, const std::vector<JobPtr> &jobs);
    const JobTimes1D &get_seq(const int &m1, const int &m2)
    {
        return this->sorted_maps[std::make_tuple(m1, m2)];
    }
};

#endif  // TWO_MACH_HPP
