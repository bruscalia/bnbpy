#ifndef JOB_HPP
#define JOB_HPP

#include <memory>
#include <vector>

// Type alias for vector of vectors of integers
using Int1D = std::vector<int>;
using Int2D = std::vector<std::vector<int>>;
using Int3D = std::vector<std::vector<std::vector<int>>>;
using Int2DPtr = std::shared_ptr<Int2D>;
using Int3DPtr = std::shared_ptr<Int3D>;
using Int1DPtr = std::shared_ptr<Int1D>;

class Job
{
public:
    // Attributes
    int j;
    Int2DPtr p;
    Int2D r;
    Int2D q;
    Int3DPtr lat;
    Int1DPtr m;
    int L;
    int s;

    // Default constructor
    Job() : j(0), p(nullptr), r(), q(), lat(nullptr), m(nullptr), L(0), s(0) {}

    // Constructor with job ID and shared pointer to processing times
    Job(const int &j_, const Int2DPtr &p_)
        : j(j_), p(p_), r(), q(),
        lat(std::make_shared<Int3D>(p_->size())),
        m(std::make_shared<Int1D>(p_->size())), L(p_->size()), s(1)
    {
        fill_m(p_);
        initialize(p_);
    }

    // Constructor with job ID and shared pointer to processing times
    Job(const int &j_, const Int2DPtr &p_, const int s_)
        : j(j_), p(p_), r(), q(),
        lat(std::make_shared<Int3D>(p_->size())),
        m(std::make_shared<Int1D>(p_->size())), L(p_->size()), s(s_)
    {
        fill_m(p_);
        initialize(p_);
    }

    // Constructor with job ID and vector for processing times (creates
    // shared_ptr internally)
    Job(const int &j_, const Int2D &p_)
        : j(j_),
          p(std::make_shared<Int2D>(p_)),
          r(),
          q(),
          lat(std::make_shared<Int3D>(p_.size())),
          m(std::make_shared<Int1D>(p_.size())),
          L(p_.size()),
          s(1)
    {
        fill_m(p);
        initialize(p);
    }

    // Constructor with job ID and vector for processing times (creates
    // shared_ptr internally)
    Job(const int &j_, const Int2D &p_, const int s_)
        : j(j_),
          p(std::make_shared<Int2D>(p_)),
          r(),
          q(),
          lat(std::make_shared<Int3D>(p_.size())),
          m(std::make_shared<Int1D>(p_.size())),
          L(p_.size()),
          s(s_)
    {
        fill_m(p);
        initialize(p);
    }

    // Parameterized constructor -> deepcopy of arrays
    Job(const int &j_, const Int2DPtr &p_, const Int2D &r_, const Int2D &q_,
        const Int3DPtr &lat_, const Int1DPtr &m_, const int s_)
        : j(j_), p(p_), r(r_), q(q_), lat(lat_), m(m_), L(p_->size()), s(s_)
    {
    }

    // Parameterized constructor -> deepcopy of arrays
    Job(const int &j_, const Int2DPtr &p_, const Int2D &r_, const Int2D &q_,
        const Int3DPtr &lat_, const Int1DPtr &m_)
        : j(j_), p(p_), r(r_), q(q_), lat(lat_), m(m_), L(p_->size()), s(1)
    {
    }

    // Destructor
    ~Job() {}

    // Get total time
    int get_T() const;

private:
    void initialize(const Int2DPtr &p_);
    inline void fill_m(const Int2DPtr &p_) {
        for (size_t i = 0; i < p_->size(); ++i) {
            (*m)[i] = p_->at(i).size();
        }
    }
};

// Function to copy a job
inline std::shared_ptr<Job> copy_job(const std::shared_ptr<Job> &jobptr);

// Function to copy a vector of jobs
std::vector<std::shared_ptr<Job>> copy_jobs(
    const std::vector<std::shared_ptr<Job>> &jobs);

// Type definition for shared pointer
typedef std::shared_ptr<Job> JobPtr;

#endif  // JOB_HPP