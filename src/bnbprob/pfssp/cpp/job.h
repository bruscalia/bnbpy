#ifndef JOB_H
#define JOB_H

#include <vector>

class Job {
public:
    // Attributes
    const int j;                        // Id
    const std::vector<int> p;                       // Processing times
    std::vector<int> r;           // Release time
    std::vector<int> q;           // Wait time
    std::vector<std::vector<int>> lat;                    // Latency
    int slope;                    // Slope
    int T;                        // Total time

    // Constructor
    Job();  // Construtor padrão

    // Destrutor
    // ~Job();
};

#endif // JOB_H
