#define CATCH_CONFIG_MAIN
#include "catch2/catch_test_macros.hpp"

#include "job.hpp"
#include "mach_graph.hpp"

TEST_CASE("Job basic construction and properties", "[job]")
{
    SECTION("Simple sequential machine graph")
    {
        // Create a simple sequential machine graph: 0 -> 1 -> 2
        int M = 3;
        std::vector<std::vector<int>> prec = {{}, {0}, {1}};
        std::vector<std::vector<int>> succ = {{1}, {2}, {}};
        std::vector<int> topo_order = {0, 1, 2};
        std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};

        MachineGraph mach_graph(M, prec, succ, topo_order, descendants);

        // Create a job with processing times [3, 5, 2]
        std::vector<int> processing_times = {3, 5, 2};
        Job job(0, processing_times, mach_graph);

        SECTION("Job ID is correct")
        {
            REQUIRE(job.j == 0);
        }

        SECTION("Processing times are stored correctly")
        {
            REQUIRE(job.p.size() == 3);
            REQUIRE(job.p[0] == 3);
            REQUIRE(job.p[1] == 5);
            REQUIRE(job.p[2] == 2);
        }

        SECTION("Total processing time is correct")
        {
            REQUIRE(job.get_T() == 10);
        }

        SECTION("Release dates are computed correctly")
        {
            REQUIRE(job.r.size() == 3);
            REQUIRE(job.r[0] == 0);  // First machine has no predecessors
            REQUIRE(job.r[1] == 3);  // Must wait for machine 0 to finish (0 + 3)
            REQUIRE(job.r[2] == 8);  // Must wait for machine 1 to finish (3 + 5)
        }

        SECTION("Wait times are computed correctly")
        {
            REQUIRE(job.q.size() == 3);
            REQUIRE(job.q[0] == 7);  // 5 + 2 (wait for machines 1 and 2)
            REQUIRE(job.q[1] == 2);  // 2 (wait for machine 2)
            REQUIRE(job.q[2] == 0);  // Last machine has no successors
        }

        SECTION("Latency matrix has correct dimensions")
        {
            REQUIRE(job.lat.size() == 3);
            for (int i = 0; i < 3; ++i)
            {
                REQUIRE(job.lat[i].size() == 3);
            }
        }

        SECTION("Latency values are correct for sequential graph")
        {
            // lat[i][j] = longest path from i to j minus p[i]
            REQUIRE(job.lat[0][0] == 0);  // Same machine
            REQUIRE(job.lat[0][1] == 0);  // Direct successor, lat = p[0] - p[0] = 0
            REQUIRE(job.lat[0][2] == 5);  // lat = (p[0] + p[1]) - p[0] = 5
            REQUIRE(job.lat[1][1] == 0);  // Same machine
            REQUIRE(job.lat[1][2] == 0);  // Direct successor
            REQUIRE(job.lat[2][2] == 0);  // Same machine
        }
    }

    SECTION("Parallel machine graph")
    {
        // Create a fork-join graph: 0 -> {1, 2} (parallel)
        int M = 3;
        std::vector<std::vector<int>> prec = {{}, {0}, {0}};
        std::vector<std::vector<int>> succ = {{1, 2}, {}, {}};
        std::vector<int> topo_order = {0, 1, 2};
        std::vector<std::vector<int>> descendants = {{1, 2}, {}, {}};

        MachineGraph mach_graph(M, prec, succ, topo_order, descendants);

        std::vector<int> processing_times = {4, 3, 6};
        Job job(1, processing_times, mach_graph);

        SECTION("Job ID is correct")
        {
            REQUIRE(job.j == 1);
        }

        SECTION("Release dates for parallel operations")
        {
            REQUIRE(job.r[0] == 0);
            REQUIRE(job.r[1] == 4);  // Both wait for machine 0
            REQUIRE(job.r[2] == 4);
        }

        SECTION("Wait times for parallel operations")
        {
            REQUIRE(job.q[0] == 6);  // Max of successors (max(3, 6) = 6)
            REQUIRE(job.q[1] == 0);  // No successors
            REQUIRE(job.q[2] == 0);  // No successors
        }

        SECTION("Latency for parallel branches")
        {
            REQUIRE(job.lat[0][1] == 0);  // Direct successor
            REQUIRE(job.lat[0][2] == 0);  // Direct successor
            REQUIRE(job.lat[1][0] == 0);  // No path from 1 to 0
            REQUIRE(job.lat[2][0] == 0);  // No path from 2 to 0
        }
    }

    SECTION("Assembly-disassembly machine graph")
    {
        // Paths: 0 -> 1 -> 2, 0 -> 3 -> 4 -> 2, and 1 -> 4
        int M = 5;
        std::vector<std::vector<int>> prec = {{}, {0}, {1, 4}, {0}, {1, 3}};
        std::vector<std::vector<int>> succ = {{1, 3}, {2, 4}, {}, {4}, {2}};
        std::vector<int> topo_order = {0, 1, 3, 4, 2};
        std::vector<std::vector<int>> descendants = {{1, 2, 3, 4}, {2, 4}, {}, {4, 2}, {2}};

        MachineGraph mach_graph(M, prec, succ, topo_order, descendants);

        // Processing times: [3, 5, 2, 3, 2] for machines 0, 1, 2, 3, 4
        std::vector<int> processing_times = {3, 5, 2, 3, 2};
        Job job(0, processing_times, mach_graph);

        SECTION("Job ID is correct")
        {
            REQUIRE(job.j == 0);
        }

        SECTION("Processing times are stored correctly")
        {
            REQUIRE(job.p.size() == 5);
            REQUIRE(job.p[0] == 3);
            REQUIRE(job.p[1] == 5);
            REQUIRE(job.p[2] == 2);
            REQUIRE(job.p[3] == 3);
            REQUIRE(job.p[4] == 2);
        }

        SECTION("Total processing time is correct")
        {
            REQUIRE(job.get_T() == 15);  // 3 + 5 + 2 + 3 + 2
        }

        SECTION("Release dates are computed correctly")
        {
            REQUIRE(job.r.size() == 5);
            REQUIRE(job.r[0] == 0);  // No predecessors
            REQUIRE(job.r[1] == 3);  // 0 + p[0] = 3
            REQUIRE(job.r[3] == 3);  // 0 + p[0] = 3
            REQUIRE(job.r[4] == 8);  // max(3 + p[1], 3 + p[3]) = max(8, 6) = 8
            REQUIRE(job.r[2] == 10); // max(3 + p[1], 8 + p[4]) = max(8, 10) = 10
        }

        SECTION("Wait times are computed correctly")
        {
            REQUIRE(job.q.size() == 5);
            REQUIRE(job.q[2] == 0);  // No successors
            REQUIRE(job.q[1] == 4);  // max(0 + p[2], 2 + p[4]) = max(2, 4) = 4
            REQUIRE(job.q[4] == 2);  // 0 + p[2] = 2
            REQUIRE(job.q[3] == 4);  // 2 + p[4] = 4
            REQUIRE(job.q[0] == 9);  // max(4 + p[1], 4 + p[3]) = max(9, 7) = 9
        }

        SECTION("Latency matrix has correct dimensions")
        {
            REQUIRE(job.lat.size() == 5);
            for (int i = 0; i < 5; ++i)
            {
                REQUIRE(job.lat[i].size() == 5);
            }
        }

        SECTION("Sample latency values")
        {
            // lat[i][j] = longest path from i to j minus p[i]
            REQUIRE(job.lat[0][0] == 0);  // Same machine
            REQUIRE(job.lat[0][1] == 0);  // Direct successor
            REQUIRE(job.lat[0][3] == 0);  // Direct successor
            REQUIRE(job.lat[0][2] == 7);  // Longest path 0->1->4->2: (3+5+2)-3 = 7
            REQUIRE(job.lat[1][2] == 2);  // Longest path 1->4->2: (5+2+2)-5 = 4? or 1->2 direct: 5-5=0? max is 4
        }
    }
}

TEST_CASE("Job slope computation", "[job][slope]")
{
    SECTION("Slope calculation for simple job")
    {
        int M = 3;
        std::vector<std::vector<int>> prec = {{}, {0}, {1}};
        std::vector<std::vector<int>> succ = {{1}, {2}, {}};
        std::vector<int> topo_order = {0, 1, 2};
        std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};

        MachineGraph mach_graph(M, prec, succ, topo_order, descendants);

        std::vector<int> processing_times = {2, 4, 3};
        Job job(0, processing_times, mach_graph);

        // Slope = sum((k - (m+1)/2) * p[k-1]) for k=1 to m
        // m = 3, so (m+1)/2 = 2
        // k=1: (1-2)*2 = -2
        // k=2: (2-2)*4 = 0
        // k=3: (3-2)*3 = 3
        // Total: -2 + 0 + 3 = 1
        int expected_slope = 1;
        REQUIRE(job.get_slope() == expected_slope);
    }
}

TEST_CASE("Job recompute_r_q", "[job][recompute]")
{
    SECTION("Recompute with new machine graph")
    {
        // Original graph: 0 -> 1 -> 2
        int M = 3;
        std::vector<std::vector<int>> prec1 = {{}, {0}, {1}};
        std::vector<std::vector<int>> succ1 = {{1}, {2}, {}};
        std::vector<int> topo_order1 = {0, 1, 2};
        std::vector<std::vector<int>> descendants1 = {{1, 2}, {2}, {}};

        MachineGraph mach_graph1(M, prec1, succ1, topo_order1, descendants1);

        std::vector<int> processing_times = {3, 5, 2};
        Job job(0, processing_times, mach_graph1);

        // Verify initial state
        REQUIRE(job.r[1] == 3);
        REQUIRE(job.q[0] == 7);

        // New graph: 0 -> 2 -> 1 (different order)
        std::vector<std::vector<int>> prec2 = {{}, {2}, {0}};
        std::vector<std::vector<int>> succ2 = {{2}, {}, {1}};
        std::vector<int> topo_order2 = {0, 2, 1};
        std::vector<std::vector<int>> descendants2 = {{2, 1}, {}, {1}};

        MachineGraph mach_graph2(M, prec2, succ2, topo_order2, descendants2);

        // Recompute with new graph
        job.recompute_r_q(mach_graph2);

        SECTION("Release dates updated correctly")
        {
            REQUIRE(job.r[0] == 0);
            REQUIRE(job.r[2] == 3);  // Now machine 2 follows machine 0
            REQUIRE(job.r[1] == 5);  // Machine 1 follows machine 2 (3 + 2)
        }

        SECTION("Wait times updated correctly")
        {
            REQUIRE(job.q[0] == 7);  // Still needs to wait for 2 and 1
            REQUIRE(job.q[2] == 5);  // Needs to wait for machine 1
            REQUIRE(job.q[1] == 0);  // Now last in sequence
        }
    }
}

TEST_CASE("Job with parameterized constructor", "[job][constructor]")
{
    SECTION("Create job with all parameters")
    {
        std::vector<int> p = {2, 3, 4};
        std::vector<int> r = {0, 2, 5};
        std::vector<int> q = {7, 4, 0};
        std::vector<std::vector<int>> lat = {{0, 0, 3}, {0, 0, 0}, {0, 0, 0}};
        std::vector<int> s = {0, 0, 0};

        Job job(5, p, r, q, lat, s);

        REQUIRE(job.j == 5);
        REQUIRE(job.p == p);
        REQUIRE(job.r == r);
        REQUIRE(job.q == q);
        REQUIRE(job.lat == lat);
        REQUIRE(job.s == s);
        REQUIRE(job.get_T() == 9);
    }
}
