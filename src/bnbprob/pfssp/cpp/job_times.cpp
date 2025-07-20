#include "job_times.hpp"

#include <memory>

#include "job.hpp"

JobTimes::JobTimes(const int &m1, const int &m2, const JobPtr &jobptr_)
{
    int &lat = jobptr_->lat->at(m2)[m1];
    this->t1 = jobptr_->p->at(m1) + lat;
    this->t2 = jobptr_->p->at(m2) + lat;
    this->p1 = &jobptr_->p->at(m1);
    this->p2 = &jobptr_->p->at(m2);
    this->lat = &jobptr_->lat->at(m2)[m1];
    this->jobptr = &(*jobptr_);
}
