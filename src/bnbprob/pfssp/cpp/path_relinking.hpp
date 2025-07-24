#ifndef PATH_RELINKING_HPP
#define PATH_RELINKING_HPP

#include <algorithm>
#include <unordered_set>
#include <vector>

#include "job.hpp"
#include "permutation.hpp"

struct PathSwap
{
    int position;
    int job_id;

    bool operator==(const PathSwap &other) const
    {
        return position == other.position && job_id == other.job_id;
    }
};

namespace std {
    template <>
    struct hash<PathSwap> {
        std::size_t operator()(const PathSwap& s) const noexcept {
            // Combine the hashes of position and job_id
            return std::hash<int>()(s.position) ^ (std::hash<int>()(s.job_id) << 1);
        }
    };
}

// Finds all swaps in a permutation
std::unordered_set<PathSwap> find_swaps(const Permutation &perm_a,
                                        const Permutation &perm_b);

// This function should swap two jobs in the permutation
// free jobs vector. The position should be occupied by the job
// with job_id, while the job originally at position should be moved
// to the previous position of job_id.
void apply_swap(Permutation &perm, const PathSwap &swap);

// This function should push to bottom
// all permutation free jobs
int calc_cost(Permutation &perm);

// This function should apply the swap to the permutation
Permutation path_relinking(const Permutation &a, const Permutation &b);

#endif  // PATH_RELINKING_HPP
