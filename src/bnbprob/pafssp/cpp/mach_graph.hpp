#ifndef MACH_GRAPH_HPP
#define MACH_GRAPH_HPP

#include <algorithm>
#include <iostream>
#include <limits>
#include <numeric>
#include <vector>

using namespace std;

class MachineGraph
{
private:
    // Number of machines
    int M;
    // Precedence operations
    std::vector<std::vector<int>> prec;
    // Successor operations
    std::vector<std::vector<int>> succ;
    // Topological order of machines
    std::vector<int> topo_order;
    // Reverse topological order of machines
    std::vector<int> rev_topo_order;
    // Descendants of machines
    std::vector<std::vector<int>> descendants;

public:
    // Default constructor
    MachineGraph() : M(0) {}

    // All arguments constructor
    MachineGraph(int M, const std::vector<std::vector<int>>& prec,
                 const std::vector<std::vector<int>>& succ,
                 const std::vector<int>& topo_order,
                 const std::vector<int>& rev_topo_order,
                 const std::vector<std::vector<int>>& descendants)
        : M(M),
          prec(prec),
          succ(succ),
          topo_order(topo_order),
          rev_topo_order(rev_topo_order),
          descendants(descendants)
    {
    }

    // Constructor without reverse topological order (computes it automatically)
    MachineGraph(int M, const std::vector<std::vector<int>>& prec,
                 const std::vector<std::vector<int>>& succ,
                 const std::vector<int>& topo_order,
                 const std::vector<std::vector<int>>& descendants)
        : M(M),
          prec(prec),
          succ(succ),
          topo_order(topo_order),
          descendants(descendants)
    {
        // Compute reverse topological order
        rev_topo_order = topo_order;
        std::reverse(rev_topo_order.begin(), rev_topo_order.end());
    }

    // Getters for precedence operations by index
    const std::vector<int>& get_prec(int machine_idx) const
    {
        return prec[machine_idx];
    }

    // Getters for successor operations by index
    const std::vector<int>& get_succ(int machine_idx) const
    {
        return succ[machine_idx];
    }

    // Getters for precedence operations
    const std::vector<std::vector<int>>& get_prec_all() const { return prec; }

    // Getters for successor operations
    const std::vector<std::vector<int>>& get_succ_all() const { return succ; }

    // Getter for topological order
    const std::vector<int>& get_topo_order() const { return topo_order; }

    // Getter for reverse topological order
    const std::vector<int>& get_rev_topo_order() const
    {
        return rev_topo_order;
    }

    // Getter for descendants of machines
    const std::vector<std::vector<int>>& get_descendants() const
    {
        return descendants;
    }

    // Getter for number of machines
    int get_M() const { return M; }
};

#endif  // MACH_GRAPH_HPP