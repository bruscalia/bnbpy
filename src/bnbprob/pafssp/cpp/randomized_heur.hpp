
#ifndef RANDOMIZED_HEUR_HPP
#define RANDOMIZED_HEUR_HPP

#include <vector>

#include "job.hpp"
#include "mach_graph.hpp"
#include "permutation.hpp"

// Multistart randomized heuristic: shuffle jobs, neh_core, local search, with
// optional seed
Permutation randomized_heur(std::vector<JobPtr> jobs_, int n_iter,
                            unsigned int seed,
                            const std::shared_ptr<MachineGraph> &mach_graph);

#endif  // RANDOMIZED_HEUR_HPP
