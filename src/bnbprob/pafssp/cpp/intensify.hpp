#ifndef INTENSIFY_HPP
#define INTENSIFY_HPP

#include <algorithm>
#include <memory>
#include <vector>

#include "job.hpp"
#include "local_search.hpp"
#include "mach_graph.hpp"
#include "permutation.hpp"
#include "sigma.hpp"
#include "utils.hpp"

// Intensification heuristic with constructive and local search
Permutation intensify(const Permutation &perm, const Permutation &ref_perm);

#endif  // INTENSIFY_HPP
