#include "catch2/catch_test_macros.hpp"
#include "job.hpp"
#include "job_times.hpp"
#include "mach_graph.hpp"

TEST_CASE("JobTimes construction", "[job_times]")
{
    SECTION("Manual constructor with all parameters")
    {
        // Create simple sequential machine graph
        int M = 3;
        std::vector<std::vector<int>> prec = {{}, {0}, {1}};
        std::vector<std::vector<int>> succ = {{1}, {2}, {}};
        std::vector<int> topo_order = {0, 1, 2};
        std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};

        MachineGraph mach_graph(M, prec, succ, topo_order, descendants);
        Job job(0, {3, 5, 2}, mach_graph);

        JobTimes jt(10, 15, 3, 5, 2, job);

        REQUIRE(jt.t1 == 10);
        REQUIRE(jt.t2 == 15);
        REQUIRE(jt.p1 == 3);
        REQUIRE(jt.p2 == 5);
        REQUIRE(jt.lat == 2);
        REQUIRE(jt.job.j == 0);
    }

    SECTION("Constructor from job and machine indices")
    {
        // Create simple sequential machine graph: 0 -> 1 -> 2
        int M = 3;
        std::vector<std::vector<int>> prec = {{}, {0}, {1}};
        std::vector<std::vector<int>> succ = {{1}, {2}, {}};
        std::vector<int> topo_order = {0, 1, 2};
        std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};

        MachineGraph mach_graph(M, prec, succ, topo_order, descendants);

        // Processing times: [3, 5, 2]
        Job job(0, {3, 5, 2}, mach_graph);

        SECTION("JobTimes for machines 0 and 1")
        {
            JobTimes jt(0, 1, job);

            // According to implementation:
            // t1 = p[m1] + lat[m1][m2] = 3 + 0 = 3
            // t2 = p[m2] + lat[m1][m2] = 5 + 0 = 5
            // p1 = p[m1] = 3
            // p2 = p[m2] = 5
            // lat = lat[m1][m2] = 0

            REQUIRE(jt.t1 == 3);
            REQUIRE(jt.t2 == 5);
            REQUIRE(jt.p1 == 3);
            REQUIRE(jt.p2 == 5);
            REQUIRE(jt.lat == job.lat[0][1]);
            REQUIRE(jt.job.j == 0);
        }

        SECTION("JobTimes for machines 0 and 2")
        {
            JobTimes jt(0, 2, job);

            // lat[0][2] = 5 (from job tests)
            // t1 = 3 + 5 = 8
            // t2 = 2 + 5 = 7
            REQUIRE(jt.t1 == 8);
            REQUIRE(jt.t2 == 7);
            REQUIRE(jt.p1 == 3);
            REQUIRE(jt.p2 == 2);
            REQUIRE(jt.lat == job.lat[0][2]);
        }

        SECTION("JobTimes for machines 1 and 2")
        {
            JobTimes jt(1, 2, job);

            // lat[1][2] = 0 (direct successor)
            REQUIRE(jt.t1 == 5);
            REQUIRE(jt.t2 == 2);
            REQUIRE(jt.p1 == 5);
            REQUIRE(jt.p2 == 2);
            REQUIRE(jt.lat == job.lat[1][2]);
        }
    }
}

TEST_CASE("JobTimes with different job configurations", "[job_times]")
{
    SECTION("Parallel machine graph")
    {
        // Create fork-join graph: 0 -> {1, 2} (parallel)
        int M = 3;
        std::vector<std::vector<int>> prec = {{}, {0}, {0}};
        std::vector<std::vector<int>> succ = {{1, 2}, {}, {}};
        std::vector<int> topo_order = {0, 1, 2};
        std::vector<std::vector<int>> descendants = {{1, 2}, {}, {}};

        MachineGraph mach_graph(M, prec, succ, topo_order, descendants);
        Job job(5, {4, 3, 6}, mach_graph);

        JobTimes jt(0, 1, job);

        REQUIRE(jt.job.j == 5);
        REQUIRE(jt.p1 == 4);
        REQUIRE(jt.p2 == 3);
        // t1 = p[0] + lat[0][1] = 4 + 0 = 4
        // t2 = p[1] + lat[0][1] = 3 + 0 = 3
        REQUIRE(jt.t1 == 4);
        REQUIRE(jt.t2 == 3);
    }

    SECTION("Job with different ID")
    {
        int M = 2;
        std::vector<std::vector<int>> prec = {{}, {0}};
        std::vector<std::vector<int>> succ = {{1}, {}};
        std::vector<int> topo_order = {0, 1};
        std::vector<std::vector<int>> descendants = {{1}, {}};

        MachineGraph mach_graph(M, prec, succ, topo_order, descendants);
        Job job(42, {10, 20}, mach_graph);

        JobTimes jt(0, 1, job);

        REQUIRE(jt.job.j == 42);
        REQUIRE(jt.p1 == 10);
        REQUIRE(jt.p2 == 20);
    }
}
