#include <vector>
#include <algorithm>
#include <limits>

#include "job.hpp"
#include "utils.hpp"

int SMALL = -1000000;


void recompute_r0(std::vector<JobPtr> &jobs){
    jobs[0]->r[0] = 0;
    for (int j = 1; j < jobs.size(); ++j){
        jobs[j]->r[0] = jobs[j - 1]->r[0] + jobs[j - 1]->p->at(0);
    }
}


void recompute_r0(std::vector<JobPtr> &jobs, int k){
    if (k == 0){
        return recompute_r0(jobs);
    }
    for (int j = k; j < jobs.size(); ++j){
        jobs[j]->r[0] = jobs[j - 1]->r[0] + jobs[j - 1]->p->at(0);
    }
}


int get_max_value(const int* &ptr, int &m) {
    // Check if the pointer is null or the size is zero
    if (!ptr || m <= 0) {
        return SMALL; // Return the smallest integer as an error value
    }

    int max_val = ptr[0]; // Initialize with the first element
    for (int i = 1; i < m; ++i) {
        if (ptr[i] > max_val) {
            max_val = ptr[i];
        }
    }
    return max_val;
}

int get_max_value(const std::vector<int> &vec) {
    // Check if the pointer is null or the size is zero
    int max_val = *std::max_element(vec.begin(), vec.end());
    return max_val;
}
