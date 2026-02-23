#ifndef JOB_TIMES_HPP
#define JOB_TIMES_HPP

#include <memory>

#include "job.hpp"

struct JobTimes
{
    int t1;
    int t2;
    int p1;
    int p2;
    int lat;
    Job job;

    // Constructor
    JobTimes(const int &t1_, const int &t2_, const int &p1_, const int &p2_,
             const int &lat_, const Job &job_)
        : t1(t1_), t2(t2_), p1(p1_), p2(p2_), lat(lat_), job(job_)
    {
    }

    JobTimes(const int &m1, const int &m2, const Job &job_);
};

#endif  // JOB_TIMES_HPP
