#ifndef JOB_H
#define JOB_H

#include <memory>
#include <vector>

using namespace std;

class Job {
   public:
    // Attributes
    int j;
    std::shared_ptr<std::vector<int>> p;
    std::vector<int> r;
    std::vector<int> q;
    shared_ptr<vector<vector<int>>> lat;
    int slope;
    int T;

    // Default constructor
    Job();

    // Constructor with job ID and shared pointer to processing times
    Job(int j_, std::shared_ptr<std::vector<int>> &p_);

    // Constructor with job ID and vector for processing times (creates
    // shared_ptr internally)
    Job(int j_, std::vector<int> &p_);

    // Parameterized constructor -> deepcopy of arrays
    Job(
        int j_,
        std::shared_ptr<std::vector<int>> &p_,
        vector<int> &r_,
        vector<int> &q_,
        shared_ptr<vector<vector<int>>> &lat_,
        int slope_,
        int T_
    );

    // Destructor
    ~Job();

   private:
    void initialize(std::shared_ptr<std::vector<int>> &p_);
};

// Function to copy a job
inline std::shared_ptr<Job> copy_job(const std::shared_ptr<Job> &jobptr);

// Function to copy a vector of jobs
std::vector<std::shared_ptr<Job>> copy_jobs(const std::vector<std::shared_ptr<Job>> &jobs);

// Type definition for shared pointer
typedef std::shared_ptr<Job> JobPtr;

#endif  // JOB_H
