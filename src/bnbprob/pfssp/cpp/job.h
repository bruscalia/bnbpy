#ifndef JOB_H
#define JOB_H

#include <vector>

class Job {
public:
    // Attributes
    int j;                        // Id
    int* p;                       // Processing times
    std::vector<int> r;           // Release time
    std::vector<int> q;           // Wait time
    int** lat;                    // Latency
    int slope;                    // Slope
    int T;                        // Total time

    // Constructor
    Job();  // Construtor padrão

    // Destrutor
    // ~Job();
};

#endif // JOB_H
