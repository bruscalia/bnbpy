#include "catch2/catch_test_macros.hpp"
#include "job.hpp"
#include "mach_graph.hpp"
#include "two_mach.hpp"

TEST_CASE("TwoMach - Johnson's algorithm basic", "[two_mach]")
{
    SECTION("Simple two-machine sequential problem")
    {
        // Create simple sequential graph: 0 -> 1
        int M = 2;
        std::vector<std::vector<int>> prec = {{}, {0}};
        std::vector<std::vector<int>> succ = {{1}, {}};
        std::vector<int> topo_order = {0, 1};
        std::vector<std::vector<int>> descendants = {{1}, {}};

        MachineGraph mach_graph(M, prec, succ, topo_order, descendants);

        // Create jobs with different processing times
        // Job 0: p = [3, 2], lat[0][1] = 0
        // Job 1: p = [2, 4], lat[0][1] = 0
        // Job 2: p = [4, 3], lat[0][1] = 0
        Job job0(0, {3, 2}, mach_graph);
        Job job1(1, {2, 4}, mach_graph);
        Job job2(2, {4, 3}, mach_graph);

        std::vector<JobPtr> jobs = {&job0, &job1, &job2};
        TwoMach two_mach(mach_graph, jobs);

        // Get the sequence for machines 0 and 1
        const JobTimes1D& seq = two_mach.get_seq(0, 1);

        REQUIRE(seq.size() == 3);

        // Johnson's rule:
        // Job 0: t1 = 3, t2 = 2, t1 > t2 -> goes to j2 (descending t2)
        // Job 1: t1 = 2, t2 = 4, t1 <= t2 -> goes to j1 (ascending t1)
        // Job 2: t1 = 4, t2 = 3, t1 > t2 -> goes to j2 (descending t2)

        // j1 sorted by ascending t1: [job1(t1=2)]
        // j2 sorted by descending t2: [job2(t2=3), job0(t2=2)]
        // Final: [job1, job2, job0]

        REQUIRE(seq[0].job.j == 1);
        REQUIRE(seq[1].job.j == 2);
        REQUIRE(seq[2].job.j == 0);
    }

    SECTION("All jobs prefer early processing (t1 <= t2)")
    {
        int M = 2;
        std::vector<std::vector<int>> prec = {{}, {0}};
        std::vector<std::vector<int>> succ = {{1}, {}};
        std::vector<int> topo_order = {0, 1};
        std::vector<std::vector<int>> descendants = {{1}, {}};

        MachineGraph mach_graph(M, prec, succ, topo_order, descendants);

        // All jobs have t1 <= t2
        Job job0(0, {1, 5}, mach_graph);
        Job job1(1, {2, 6}, mach_graph);
        Job job2(2, {3, 7}, mach_graph);

        std::vector<JobPtr> jobs = {&job0, &job1, &job2};
        TwoMach two_mach(mach_graph, jobs);

        const JobTimes1D& seq = two_mach.get_seq(0, 1);

        // All go to j1, sorted by ascending t1
        REQUIRE(seq.size() == 3);
        REQUIRE(seq[0].job.j == 0);  // t1 = 1
        REQUIRE(seq[1].job.j == 1);  // t1 = 2
        REQUIRE(seq[2].job.j == 2);  // t1 = 3
    }

    SECTION("All jobs prefer late processing (t1 > t2)")
    {
        int M = 2;
        std::vector<std::vector<int>> prec = {{}, {0}};
        std::vector<std::vector<int>> succ = {{1}, {}};
        std::vector<int> topo_order = {0, 1};
        std::vector<std::vector<int>> descendants = {{1}, {}};

        MachineGraph mach_graph(M, prec, succ, topo_order, descendants);

        // All jobs have t1 > t2
        Job job0(0, {5, 1}, mach_graph);
        Job job1(1, {6, 2}, mach_graph);
        Job job2(2, {7, 3}, mach_graph);

        std::vector<JobPtr> jobs = {&job0, &job1, &job2};
        TwoMach two_mach(mach_graph, jobs);

        const JobTimes1D& seq = two_mach.get_seq(0, 1);

        // All go to j2, sorted by descending t2
        REQUIRE(seq.size() == 3);
        REQUIRE(seq[0].job.j == 2);  // t2 = 3 (highest)
        REQUIRE(seq[1].job.j == 1);  // t2 = 2
        REQUIRE(seq[2].job.j == 0);  // t2 = 1 (lowest)
    }
}

TEST_CASE("TwoMach - with latency", "[two_mach]")
{
    SECTION("Sequential graph with latency")
    {
        // Graph: 0 -> 1 -> 2
        int M = 3;
        std::vector<std::vector<int>> prec = {{}, {0}, {1}};
        std::vector<std::vector<int>> succ = {{1}, {2}, {}};
        std::vector<int> topo_order = {0, 1, 2};
        std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};

        MachineGraph mach_graph(M, prec, succ, topo_order, descendants);

        // Processing times: [3, 5, 2]
        // lat[0][1] = 0, lat[0][2] = 5, lat[1][2] = 0
        Job job0(0, {3, 5, 2}, mach_graph);
        Job job1(1, {2, 4, 3}, mach_graph);

        std::vector<JobPtr> jobs = {&job0, &job1};
        TwoMach two_mach(mach_graph, jobs);

        SECTION("Machines 0 and 2 with latency")
        {
            const JobTimes1D& seq = two_mach.get_seq(0, 2);

            REQUIRE(seq.size() == 2);

            // Job0: lat[0][2] = 5, t1 = 3 + 5 = 8, t2 = 2 + 5 = 7, t1 > t2
            // Job1: lat[0][2] = 4, t1 = 2 + 4 = 6, t2 = 3 + 4 = 7, t1 < t2

            // j1: [job1(t1=6)]
            // j2: [job0(t2=7)]
            // Final: [job1, job0]

            REQUIRE(seq[0].job.j == 1);
            REQUIRE(seq[1].job.j == 0);
        }

        SECTION("Machines 1 and 2 without significant latency")
        {
            const JobTimes1D& seq = two_mach.get_seq(1, 2);

            REQUIRE(seq.size() == 2);

            // lat[1][2] = 0 for both
            // Job0: t1 = 5, t2 = 2, t1 > t2
            // Job1: t1 = 4, t2 = 3, t1 > t2

            // Both go to j2, sorted descending by t2
            // Final: [job1(t2=3), job0(t2=2)]

            REQUIRE(seq[0].job.j == 1);
            REQUIRE(seq[1].job.j == 0);
        }
    }
}

TEST_CASE("TwoMach - constructor variants", "[two_mach]")
{
    SECTION("Constructor with MachineGraph (only valid pairs)")
    {
        int M = 3;
        std::vector<std::vector<int>> prec = {
            {}, {0}, {0}};  // Parallel: 0 -> {1, 2}
        std::vector<std::vector<int>> succ = {{1, 2}, {}, {}};
        std::vector<int> topo_order = {0, 1, 2};
        std::vector<std::vector<int>> descendants = {{1, 2}, {}, {}};

        MachineGraph mach_graph(M, prec, succ, topo_order, descendants);

        Job job0(0, {4, 3, 6}, mach_graph);
        std::vector<JobPtr> jobs = {&job0};

        // Using MachineGraph constructor - only creates pairs in precedence
        // graph
        TwoMach two_mach(mach_graph, jobs);

        // Should have pairs: (0,1), (0,2) but NOT (1,2) since 1 and 2 are
        // parallel
        const JobTimes1D& seq01 = two_mach.get_seq(0, 1);
        const JobTimes1D& seq02 = two_mach.get_seq(0, 2);

        REQUIRE(seq01.size() == 1);
        REQUIRE(seq02.size() == 1);
    }
}

TEST_CASE("TwoMach - edge cases", "[two_mach]")
{
    SECTION("Single job")
    {
        int M = 2;
        std::vector<std::vector<int>> prec = {{}, {0}};
        std::vector<std::vector<int>> succ = {{1}, {}};
        std::vector<int> topo_order = {0, 1};
        std::vector<std::vector<int>> descendants = {{1}, {}};

        MachineGraph mach_graph(M, prec, succ, topo_order, descendants);

        Job job0(0, {3, 5}, mach_graph);
        std::vector<JobPtr> jobs = {&job0};

        TwoMach two_mach(mach_graph, jobs);
        const JobTimes1D& seq = two_mach.get_seq(0, 1);

        REQUIRE(seq.size() == 1);
        REQUIRE(seq[0].job.j == 0);
    }

    SECTION("Jobs with equal t1 and t2")
    {
        int M = 2;
        std::vector<std::vector<int>> prec = {{}, {0}};
        std::vector<std::vector<int>> succ = {{1}, {}};
        std::vector<int> topo_order = {0, 1};
        std::vector<std::vector<int>> descendants = {{1}, {}};

        MachineGraph mach_graph(M, prec, succ, topo_order, descendants);

        // Job with equal processing times
        Job job0(0, {3, 3}, mach_graph);
        Job job1(1, {5, 5}, mach_graph);

        std::vector<JobPtr> jobs = {&job0, &job1};
        TwoMach two_mach(mach_graph, jobs);

        const JobTimes1D& seq = two_mach.get_seq(0, 1);

        // Both have t1 == t2, so t1 <= t2 is true, go to j1
        // Sorted by ascending t1: job0(3), job1(5)
        REQUIRE(seq.size() == 2);
        REQUIRE(seq[0].job.j == 0);
        REQUIRE(seq[1].job.j == 1);
    }
}

TEST_CASE("TwoMach - verify JobTimes properties", "[two_mach]")
{
    SECTION("Check stored JobTimes values")
    {
        int M = 2;
        std::vector<std::vector<int>> prec = {{}, {0}};
        std::vector<std::vector<int>> succ = {{1}, {}};
        std::vector<int> topo_order = {0, 1};
        std::vector<std::vector<int>> descendants = {{1}, {}};

        MachineGraph mach_graph(M, prec, succ, topo_order, descendants);

        Job job0(0, {3, 5}, mach_graph);
        std::vector<JobPtr> jobs = {&job0};

        TwoMach two_mach(mach_graph, jobs);
        const JobTimes1D& seq = two_mach.get_seq(0, 1);

        REQUIRE(seq.size() == 1);

        const JobTimes& jt = seq[0];
        REQUIRE(jt.job.j == 0);
        REQUIRE(jt.p1 == 3);
        REQUIRE(jt.p2 == 5);
        REQUIRE(jt.t1 == 3);  // p1 + lat (lat = 0)
        REQUIRE(jt.t2 == 5);  // p2 + lat
        REQUIRE(jt.lat == 0);
    }
}
