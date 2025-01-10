#ifndef JOB_H
#define JOB_H

#include <vector>

struct Job {
    int j;                          // Single integer value
    int* p;                         // Pointer to an integer
    std::vector<int> r;             // Vector of integers
    std::vector<int> q;             // Vector of integers
    int** lat;                      // Pointer to a pointer (2D array or similar)
    int slope;                      // Single integer value
    int T;                          // Single integer value

    // Default (empty) constructor
    Job()
        : j(0), p(nullptr), r(), q(), lat(nullptr), slope(0), T(0) {}

    // Constructor
    Job(int j_, int* p_, const std::vector<int>& r_, const std::vector<int>& q_, int** lat_, int slope_, int T_)
        : j(j_), p(p_), r(r_), q(q_), lat(lat_), slope(slope_), T(T_) {}

    // Destructor
    ~Job() {
        // Free memory for `p` and `lat` if dynamically allocated
        delete p;
        if (lat != nullptr) {
            // Assuming `lat` is dynamically allocated, free memory
            for (int i = 0; lat[i] != nullptr; ++i) {
                delete[] lat[i];
            }
            delete[] lat;
        }
    }
};

#endif // JOB_H
