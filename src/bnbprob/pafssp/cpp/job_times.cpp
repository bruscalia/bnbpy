#include "job_times.hpp"

#include <memory>

#include "job.hpp"

JobTimes::JobTimes(const int &m1, const int &m2, const Job &job_)
    : t1(job_.p.at(m1) + job_.lat.at(m1)[m2]),
      t2(job_.p.at(m2) + job_.lat.at(m1)[m2]),
      p1(job_.p.at(m1)),
      p2(job_.p.at(m2)),
      lat(job_.lat.at(m1)[m2]),
      j(job_.j)
{
}
