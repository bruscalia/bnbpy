#ifndef JOB_H
#define JOB_H

#include <memory>
#include <vector>

using namespace std;

class Job {
   public:
    // Attributes
    int j;                                // Job ID
    std::shared_ptr<std::vector<int>> p;  // Processing times (vector)
    vector<int> r;                        // Resource requirements (vector)
    vector<int> q;                        // Queue requirements (vector)
    shared_ptr<vector<vector<int>>> lat;  // Latency matrix (2D vector)
    int slope;                            // Slope (int)
    int T;                                // Total processing time (int)

    // Constructor with job ID and shared pointer to processing times
    Job(int j_, std::shared_ptr<std::vector<int>> &p_);

    // Constructor with job ID and vector for processing times (creates
    // shared_ptr internally)
    Job(int j_, std::vector<int> &p_);

    // Parameterized constructor
    Job(int j_, std::shared_ptr<std::vector<int>> &p_, vector<int> r_,
        vector<int> q_, shared_ptr<vector<vector<int>>> &lat_, int slope_,
        int T_);

   private:
    void initialize(std::shared_ptr<std::vector<int>> &p_);
};

// Function to start a job with a given job ID and processing times
inline std::shared_ptr<Job> start_job(int &j, std::vector<int> &p);

// Function to copy a job
inline std::shared_ptr<Job> copy_job(std::shared_ptr<Job> &jobptr);

// Function to copy a vector of jobs
std::vector<std::shared_ptr<Job>> copy_jobs(std::vector<std::shared_ptr<Job>> &jobs);

#endif  // JOB_H
