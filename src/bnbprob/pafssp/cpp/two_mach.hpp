#ifndef TWO_MACH_HPP
#define TWO_MACH_HPP

#include <memory>
#include <stdexcept>
#include <vector>

#include "job.hpp"
#include "job_times.hpp"
#include "mach_graph.hpp"

using JobTimes1D = std::vector<JobTimes>;

class TwoMach
{
private:
    int M;
    // Johnson-ordered sequences indexed by m1 * M + m2
    std::vector<JobTimes1D> sorted_seqs;
    // Whether (m1, m2) is a machine-graph pair (m2 descendant of m1)
    std::vector<bool> is_pair;
    JobTimes1D create_pair_seq(const int &m1, const int &m2,
                               const std::vector<JobPtr> &jobs);

public:
    TwoMach() : M(0) {}
    TwoMach(const MachineGraph &mach_graph, const std::vector<JobPtr> &jobs);
    // Throws std::out_of_range if (m1, m2) is not a machine-graph pair
    const JobTimes1D &get_seq(const int &m1, const int &m2) const
    {
        if (m1 < 0 || m2 < 0 || m1 >= this->M || m2 >= this->M ||
            !this->is_pair[m1 * this->M + m2])
        {
            throw std::out_of_range("Not a machine-graph pair");
        }
        return this->sorted_seqs[m1 * this->M + m2];
    }
};

#endif  // TWO_MACH_HPP
