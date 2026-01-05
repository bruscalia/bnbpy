#include "catch2/catch_test_macros.hpp"
#include "job.hpp"
#include "mach_graph.hpp"
#include "sigma.hpp"

TEST_CASE("Sigma basic construction", "[sigma]")
{
    SECTION("Default constructor")
    {
        Sigma sigma;
        REQUIRE(sigma.m == 0);
        REQUIRE(sigma.C.empty());
    }

    SECTION("Constructor with machine count and graph")
    {
        int M = 3;
        std::vector<std::vector<int>> prec = {{}, {0}, {1}};
        std::vector<std::vector<int>> succ = {{1}, {2}, {}};
        std::vector<int> topo_order = {0, 1, 2};
        std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};

        MachineGraph mach_graph(M, prec, succ, topo_order, descendants);
        Sigma sigma(M, &mach_graph);

        REQUIRE(sigma.m == 3);
        REQUIRE(sigma.C.size() == 3);
        REQUIRE(sigma.C[0] == 0);
        REQUIRE(sigma.C[1] == 0);
        REQUIRE(sigma.C[2] == 0);
        REQUIRE(sigma.get_jobs().empty());
    }

    SECTION("Constructor with shared_ptr to machine graph")
    {
        int M = 2;
        std::vector<std::vector<int>> prec = {{}, {0}};
        std::vector<std::vector<int>> succ = {{1}, {}};
        std::vector<int> topo_order = {0, 1};
        std::vector<std::vector<int>> descendants = {{1}, {}};

        auto mach_graph = std::make_shared<MachineGraph>(
            M, prec, succ, topo_order, descendants);
        Sigma sigma(M, mach_graph);

        REQUIRE(sigma.m == 2);
        REQUIRE(sigma.C.size() == 2);
    }
}

TEST_CASE("Sigma with jobs - sequential graph", "[sigma]")
{
    // Create simple sequential machine graph: 0 -> 1 -> 2
    int M = 3;
    std::vector<std::vector<int>> prec = {{}, {0}, {1}};
    std::vector<std::vector<int>> succ = {{1}, {2}, {}};
    std::vector<int> topo_order = {0, 1, 2};
    std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};

    MachineGraph mach_graph(M, prec, succ, topo_order, descendants);

    SECTION("Constructor with jobs")
    {
        Job job1(0, {2, 3, 1}, mach_graph);
        Job job2(1, {1, 2, 4}, mach_graph);

        std::vector<JobPtr> jobs = {&job1, &job2};
        Sigma sigma(M, jobs, &mach_graph);

        REQUIRE(sigma.m == 3);
        REQUIRE(sigma.get_jobs().size() == 2);
        REQUIRE(sigma.n_jobs() == 2);
    }

    SECTION("Add job to bottom of empty sequence")
    {
        Sigma sigma(M, &mach_graph);
        Job job(0, {2, 3, 1}, mach_graph);

        sigma.job_to_bottom(&job);

        REQUIRE(sigma.n_jobs() == 1);
        REQUIRE(sigma.C[0] == 2);  // r[0]=0, p[0]=2
        REQUIRE(sigma.C[1] == 5);  // max(C[0]=2, r[1]=2) + p[1]=3 = 5
        REQUIRE(sigma.C[2] == 6);  // max(C[1]=5, r[2]=5) + p[2]=1 = 6
    }

    SECTION("Add multiple jobs to bottom")
    {
        Sigma sigma(M, &mach_graph);
        Job job1(0, {2, 3, 1}, mach_graph);
        Job job2(1, {1, 2, 4}, mach_graph);

        sigma.job_to_bottom(&job1);
        sigma.job_to_bottom(&job2);

        REQUIRE(sigma.n_jobs() == 2);
        // After job1: C = [2, 5, 6]
        // After job2: C[0] = max(2, 0) + 1 = 3
        //             C[1] = max(3, 5) + 2 = 7
        //             C[2] = max(7, 6) + 4 = 11
        REQUIRE(sigma.C[0] == 3);
        REQUIRE(sigma.C[1] == 7);
        REQUIRE(sigma.C[2] == 11);
    }

    SECTION("Add job to top of empty sequence")
    {
        Sigma sigma(M, &mach_graph);
        Job job(0, {2, 3, 1}, mach_graph);

        sigma.job_to_top(&job);

        REQUIRE(sigma.n_jobs() == 1);
        // Working backwards from end
        REQUIRE(sigma.C[2] == 1);  // q[2]=0, p[2]=1
        REQUIRE(sigma.C[1] == 4);  // max(C[2]=1, q[1]=1) + p[1]=3 = 4
        REQUIRE(sigma.C[0] == 6);  // max(C[1]=4, q[0]=4) + p[0]=2 = 6
    }

    SECTION("Add multiple jobs to top")
    {
        Sigma sigma(M, &mach_graph);
        Job job1(0, {2, 3, 1}, mach_graph);
        Job job2(1, {1, 2, 4}, mach_graph);

        sigma.job_to_top(&job1);
        sigma.job_to_top(&job2);

        REQUIRE(sigma.n_jobs() == 2);
        // job2 goes to top first (becomes first), then job1 is inserted before
        // it
        std::vector<JobPtr> jobs = sigma.get_jobs();
        REQUIRE(jobs[0]->j == 1);  // job2 first
        REQUIRE(jobs[1]->j == 0);  // job1 second
    }
}

TEST_CASE("Sigma - makespan", "[sigma]")
{
    // Create simple sequential machine graph: 0 -> 1
    int M = 2;
    std::vector<std::vector<int>> prec = {{}, {0}};
    std::vector<std::vector<int>> succ = {{1}, {}};
    std::vector<int> topo_order = {0, 1};
    std::vector<std::vector<int>> descendants = {{1}, {}};

    MachineGraph mach_graph(M, prec, succ, topo_order, descendants);

    SECTION("Makespan of empty sequence")
    {
        Sigma sigma(M, &mach_graph);
        int makespan = *std::max_element(sigma.C.begin(), sigma.C.end());
        REQUIRE(makespan == 0);
    }

    SECTION("Makespan with jobs")
    {
        Sigma sigma(M, &mach_graph);
        Job job1(0, {3, 5}, mach_graph);
        Job job2(1, {2, 4}, mach_graph);

        sigma.job_to_bottom(&job1);
        sigma.job_to_bottom(&job2);

        // Makespan is max of completion times
        int makespan = *std::max_element(sigma.C.begin(), sigma.C.end());
        REQUIRE(makespan == std::max(sigma.C[0], sigma.C[1]));
    }
}

TEST_CASE("Sigma - parallel machine graph", "[sigma]")
{
    // Create fork-join graph: 0 -> {1, 2} (parallel)
    int M = 3;
    std::vector<std::vector<int>> prec = {{}, {0}, {0}};
    std::vector<std::vector<int>> succ = {{1, 2}, {}, {}};
    std::vector<int> topo_order = {0, 1, 2};
    std::vector<std::vector<int>> descendants = {{1, 2}, {}, {}};

    MachineGraph mach_graph(M, prec, succ, topo_order, descendants);

    SECTION("Add job to bottom with parallel machines")
    {
        Sigma sigma(M, &mach_graph);
        Job job(0, {4, 3, 6}, mach_graph);

        sigma.job_to_bottom(&job);

        REQUIRE(sigma.n_jobs() == 1);
        REQUIRE(sigma.C[0] == 4);  // First machine
        REQUIRE(sigma.C[1] == 7);  // 4 + 3 (depends on machine 0)
        REQUIRE(sigma.C[2] == 10);  // 4 + 6 (depends on machine 0)
    }
}
