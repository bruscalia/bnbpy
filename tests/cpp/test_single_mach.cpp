#include "catch2/catch_test_macros.hpp"
#include "job.hpp"
#include "mach_graph.hpp"
#include "single_mach.hpp"

TEST_CASE("SingleMach - constructors", "[single_mach]")
{
    SECTION("Default constructor")
    {
        SingleMach sm;

        REQUIRE(sm.r.empty());
        REQUIRE(sm.q.empty());
        REQUIRE(sm.p.empty());
    }

    SECTION("Constructor with machine count")
    {
        SingleMach sm(3);

        REQUIRE(sm.r.size() == 3);
        REQUIRE(sm.q.size() == 3);
        REQUIRE(sm.p.size() == 3);

        // r and q initialized to SHRT_MAX, p to 0
        REQUIRE(sm.r[0] == SHRT_MAX);
        REQUIRE(sm.r[1] == SHRT_MAX);
        REQUIRE(sm.r[2] == SHRT_MAX);

        REQUIRE(sm.q[0] == SHRT_MAX);
        REQUIRE(sm.q[1] == SHRT_MAX);
        REQUIRE(sm.q[2] == SHRT_MAX);

        REQUIRE(sm.p[0] == 0);
        REQUIRE(sm.p[1] == 0);
        REQUIRE(sm.p[2] == 0);
    }

    SECTION("Constructor with all arguments")
    {
        std::vector<int> r = {0, 5, 10};
        std::vector<int> q = {15, 10, 0};
        std::vector<int> p = {3, 5, 2};

        SingleMach sm(r, q, p);

        REQUIRE(sm.r == r);
        REQUIRE(sm.q == q);
        REQUIRE(sm.p == p);
    }
}

TEST_CASE("SingleMach - constructor from jobs", "[single_mach]")
{
    SECTION("Empty job list")
    {
        int M = 3;
        std::vector<std::vector<int>> prec = {{}, {0}, {1}};
        std::vector<std::vector<int>> succ = {{1}, {2}, {}};
        std::vector<int> topo_order = {0, 1, 2};
        std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};

        MachineGraph mach_graph(M, prec, succ, topo_order, descendants);
        std::vector<JobPtr> jobs = {};

        SingleMach sm(M, jobs);

        REQUIRE(sm.r.size() == 3);
        REQUIRE(sm.q.size() == 3);
        REQUIRE(sm.p.size() == 3);

        // With empty jobs, all should be 0
        REQUIRE(sm.r[0] == 0);
        REQUIRE(sm.r[1] == 0);
        REQUIRE(sm.r[2] == 0);
        REQUIRE(sm.q[0] == 0);
        REQUIRE(sm.q[1] == 0);
        REQUIRE(sm.q[2] == 0);
        REQUIRE(sm.p[0] == 0);
        REQUIRE(sm.p[1] == 0);
        REQUIRE(sm.p[2] == 0);
    }

    SECTION("Single job")
    {
        int M = 3;
        std::vector<std::vector<int>> prec = {{}, {0}, {1}};
        std::vector<std::vector<int>> succ = {{1}, {2}, {}};
        std::vector<int> topo_order = {0, 1, 2};
        std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};

        MachineGraph mach_graph(M, prec, succ, topo_order, descendants);

        // Job with p = [3, 5, 2], r = [0, 3, 8], q = [7, 2, 0]
        Job job(0, {3, 5, 2}, mach_graph);
        std::vector<JobPtr> jobs = {&job};

        SingleMach sm(M, jobs);

        // r should be min across jobs (only one job)
        REQUIRE(sm.r[0] == 0);
        REQUIRE(sm.r[1] == 3);
        REQUIRE(sm.r[2] == 8);

        // q should be min across jobs (only one job)
        REQUIRE(sm.q[0] == 7);
        REQUIRE(sm.q[1] == 2);
        REQUIRE(sm.q[2] == 0);

        // p should be sum across jobs (only one job)
        REQUIRE(sm.p[0] == 3);
        REQUIRE(sm.p[1] == 5);
        REQUIRE(sm.p[2] == 2);
    }

    SECTION("Multiple jobs - min r, min q, sum p")
    {
        int M = 3;
        std::vector<std::vector<int>> prec = {{}, {0}, {1}};
        std::vector<std::vector<int>> succ = {{1}, {2}, {}};
        std::vector<int> topo_order = {0, 1, 2};
        std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};

        MachineGraph mach_graph(M, prec, succ, topo_order, descendants);

        // Job 0: p = [3, 5, 2], r = [0, 3, 8], q = [7, 2, 0]
        Job job0(0, {3, 5, 2}, mach_graph);

        // Job 1: p = [2, 4, 3], r = [0, 2, 6], q = [7, 3, 0]
        Job job1(1, {2, 4, 3}, mach_graph);

        std::vector<JobPtr> jobs = {&job0, &job1};

        SingleMach sm(M, jobs);

        // r should be min across jobs
        REQUIRE(sm.r[0] == 0);  // min(0, 0)
        REQUIRE(sm.r[1] == 2);  // min(3, 2)
        REQUIRE(sm.r[2] == 6);  // min(8, 6)

        // q should be min across jobs
        REQUIRE(sm.q[0] == 7);  // min(7, 7)
        REQUIRE(sm.q[1] == 2);  // min(2, 3)
        REQUIRE(sm.q[2] == 0);  // min(0, 0)

        // p should be sum across jobs
        REQUIRE(sm.p[0] == 5);  // 3 + 2
        REQUIRE(sm.p[1] == 9);  // 5 + 4
        REQUIRE(sm.p[2] == 5);  // 2 + 3
    }
}

TEST_CASE("SingleMach - get_bound methods", "[single_mach]")
{
    SECTION("Get bound for specific machine")
    {
        std::vector<int> r = {0, 5, 10};
        std::vector<int> q = {15, 10, 5};
        std::vector<int> p = {3, 5, 2};

        SingleMach sm(r, q, p);

        // bound[k] = r[k] + p[k] + q[k]
        REQUIRE(sm.get_bound(0) == 0 + 3 + 15);  // 18
        REQUIRE(sm.get_bound(1) == 5 + 5 + 10);  // 20
        REQUIRE(sm.get_bound(2) == 10 + 2 + 5);  // 17
    }

    SECTION("Get maximum bound across all machines")
    {
        std::vector<int> r = {0, 5, 10};
        std::vector<int> q = {15, 10, 5};
        std::vector<int> p = {3, 5, 2};

        SingleMach sm(r, q, p);

        // bounds: [18, 20, 17], max = 20
        REQUIRE(sm.get_bound() == 20);
    }

    SECTION("Get bound with all zeros")
    {
        std::vector<int> r = {0, 0, 0};
        std::vector<int> q = {0, 0, 0};
        std::vector<int> p = {0, 0, 0};

        SingleMach sm(r, q, p);

        REQUIRE(sm.get_bound(0) == 0);
        REQUIRE(sm.get_bound(1) == 0);
        REQUIRE(sm.get_bound(2) == 0);
        REQUIRE(sm.get_bound() == 0);
    }

    SECTION("Get bound from constructed job cache")
    {
        int M = 3;
        std::vector<std::vector<int>> prec = {{}, {0}, {1}};
        std::vector<std::vector<int>> succ = {{1}, {2}, {}};
        std::vector<int> topo_order = {0, 1, 2};
        std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};

        MachineGraph mach_graph(M, prec, succ, topo_order, descendants);

        Job job(0, {3, 5, 2}, mach_graph);
        std::vector<JobPtr> jobs = {&job};

        SingleMach sm(M, jobs);

        // For single job: r = [0, 3, 8], q = [7, 2, 0], p = [3, 5, 2]
        // bounds: [0+3+7=10, 3+5+2=10, 8+2+0=10]
        REQUIRE(sm.get_bound(0) == 10);
        REQUIRE(sm.get_bound(1) == 10);
        REQUIRE(sm.get_bound(2) == 10);
        REQUIRE(sm.get_bound() == 10);
    }
}

TEST_CASE("SingleMach - update_p method", "[single_mach]")
{
    SECTION("Update p by removing a job")
    {
        int M = 3;
        std::vector<std::vector<int>> prec = {{}, {0}, {1}};
        std::vector<std::vector<int>> succ = {{1}, {2}, {}};
        std::vector<int> topo_order = {0, 1, 2};
        std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};

        MachineGraph mach_graph(M, prec, succ, topo_order, descendants);

        Job job0(0, {3, 5, 2}, mach_graph);
        Job job1(1, {2, 4, 3}, mach_graph);

        std::vector<JobPtr> jobs = {&job0, &job1};

        SingleMach sm(M, jobs);

        // Initial p: [5, 9, 5]
        REQUIRE(sm.p[0] == 5);
        REQUIRE(sm.p[1] == 9);
        REQUIRE(sm.p[2] == 5);

        // Remove job0 (p = [3, 5, 2])
        sm.update_p(&job0);

        // After removal: [5-3=2, 9-5=4, 5-2=3]
        REQUIRE(sm.p[0] == 2);
        REQUIRE(sm.p[1] == 4);
        REQUIRE(sm.p[2] == 3);
    }

    SECTION("Update p multiple times")
    {
        std::vector<int> r = {0, 0, 0};
        std::vector<int> q = {0, 0, 0};
        std::vector<int> p = {10, 15, 20};

        SingleMach sm(r, q, p);

        int M = 3;
        std::vector<std::vector<int>> prec = {{}, {0}, {1}};
        std::vector<std::vector<int>> succ = {{1}, {2}, {}};
        std::vector<int> topo_order = {0, 1, 2};
        std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};

        MachineGraph mach_graph(M, prec, succ, topo_order, descendants);

        Job job0(0, {3, 5, 2}, mach_graph);
        Job job1(1, {2, 4, 3}, mach_graph);

        sm.update_p(&job0);
        REQUIRE(sm.p[0] == 7);  // 10 - 3
        REQUIRE(sm.p[1] == 10);  // 15 - 5
        REQUIRE(sm.p[2] == 18);  // 20 - 2

        sm.update_p(&job1);
        REQUIRE(sm.p[0] == 5);  // 7 - 2
        REQUIRE(sm.p[1] == 6);  // 10 - 4
        REQUIRE(sm.p[2] == 15);  // 18 - 3
    }

    SECTION("Bound changes after update_p")
    {
        std::vector<int> r = {0, 0, 0};
        std::vector<int> q = {5, 5, 5};
        std::vector<int> p = {10, 10, 10};

        SingleMach sm(r, q, p);

        // Initial bound: max(0+10+5, 0+10+5, 0+10+5) = 15
        REQUIRE(sm.get_bound() == 15);

        int M = 3;
        std::vector<std::vector<int>> prec = {{}, {0}, {1}};
        std::vector<std::vector<int>> succ = {{1}, {2}, {}};
        std::vector<int> topo_order = {0, 1, 2};
        std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};

        MachineGraph mach_graph(M, prec, succ, topo_order, descendants);

        Job job(0, {3, 5, 2}, mach_graph);
        sm.update_p(&job);

        // After removal: p = [7, 5, 8]
        // New bound: max(0+7+5=12, 0+5+5=10, 0+8+5=13) = 13
        REQUIRE(sm.get_bound() == 13);
    }
}
