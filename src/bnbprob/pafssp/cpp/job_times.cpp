#include "job_times.hpp"

#include <memory>

#include "job.hpp"

JobTimes::JobTimes(const int &m1, const int &m2, const Job &job_)
{
    int lat = job_.lat.at(m1)[m2];
    this->t1 = job_.p.at(m1) + lat;
    this->t2 = job_.p.at(m2) + lat;
    this->p1 = job_.p.at(m1);
    this->p2 = job_.p.at(m2);
    this->lat = job_.lat.at(m1)[m2];
    this->job = job_;
}
