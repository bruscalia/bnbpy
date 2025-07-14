#ifndef JOB_TIMES_HPP
#define JOB_TIMES_HPP

#include <memory>

#include "job.hpp"

struct JobTimes
{
    int t1;
    int t2;
    const int *p1;
    const int *p2;
    const int *lat;
    const Job *jobptr;

    // Constructor
    JobTimes(const int &t1_, const int &t2_, const int *&p1_, const int *&p2_,
             const int *&lat_, const JobPtr &jobptr_)
        : t1(t1_), t2(t2_), p1(p1_), p2(p2_), lat(lat_), jobptr(&(*jobptr_))
    {
    }

    JobTimes(const int &t1_, const int &t2_, const int &p1_, const int &p2_,
             const int &lat_, const JobPtr &jobptr_)
        : t1(t1_), t2(t2_), p1(&p1_), p2(&p2_), lat(&lat_), jobptr(&(*jobptr_))
    {
    }

    JobTimes(const int &m1, const int &m2, const JobPtr &jobptr_);
};

// Type definition for shared pointer
typedef std::shared_ptr<JobTimes> JobTimesPtr;

#endif  // JOB_TIMES_HPP
