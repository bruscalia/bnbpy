#ifndef SIGMA_HPP
#define SIGMA_HPP

#include <memory>
#include <vector>

#include "job.hpp"

class Sigma
{
public:
    // Attributes
    Int1DPtr m;  // Number of machines on each parallel semiline
    std::vector<JobPtr> jobs;  // Jobs included in the sequence (permutation)
    Int2D C;  // Partial completion times for machines of each parallel semiline

    // Default constructor
    Sigma() : m(nullptr), jobs(), C() {}

    // Constructor with empty instance
    Sigma(const Int1DPtr &m_) : m(m_), jobs(), C() { fill_C(); }

    // Constructor only jobs
    Sigma(const Int1DPtr &m_, const std::vector<JobPtr> &jobs_)
        : m(m_), jobs(jobs_), C()
    {
        fill_C();
    }

    // Full constructor
    Sigma(const Int1DPtr &m_, const std::vector<JobPtr> &jobs_, const Int2D &C_)
        : m(m_), jobs(jobs_), C(C_)
    {
    }

    // Destructor
    ~Sigma() {}

    // Get cost: maximum completion time on all machines
    int cost() const;

    // Insert job at the end (bottom) of the sequence
    void job_to_bottom(const JobPtr &job);

    // Insert job at the beginning (top) of the sequence
    void job_to_top(const JobPtr &job);

private:
    // Helper function to fill C with zeros
    void fill_C()
    {
        C.clear();
        C.reserve(m->size());
        for (size_t i = 0; i < m->size(); ++i)
        {
            C.push_back(std::vector<int>(m->at(i), 0));
        }
    }
};

#endif  // SIGMA_HPP
