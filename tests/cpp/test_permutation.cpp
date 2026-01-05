#include "catch2/catch_test_macros.hpp"
#include "job.hpp"
#include "mach_graph.hpp"
#include "permutation.hpp"
#include "sigma.hpp"

TEST_CASE("Permutation - constructors", "[permutation]")
{
    SECTION("Default constructor")
    {
        Permutation perm;

        REQUIRE(perm.m == 0);
        REQUIRE(perm.n == 0);
        REQUIRE(perm.level == 0);
        REQUIRE(perm.free_jobs.empty());
    }

    SECTION("Constructor from processing times")
    {
        int M = 3;
        std::vector<std::vector<int>> prec = {{}, {0}, {1}};
        std::vector<std::vector<int>> succ = {{1}, {2}, {}};
        std::vector<int> topo_order = {0, 1, 2};
        std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};

        auto mach_graph = std::make_shared<MachineGraph>(
            M, prec, succ, topo_order, descendants);

        std::vector<std::vector<int>> p = {{3, 5, 2}, {2, 4, 3}};

        Permutation perm(p, mach_graph);

        REQUIRE(perm.m == 3);
        REQUIRE(perm.n == 2);
        REQUIRE(perm.level == 0);
        REQUIRE(perm.free_jobs.size() == 2);
        REQUIRE(perm.sigma1.get_jobs().empty());
        REQUIRE(perm.sigma2.get_jobs().empty());
    }

    SECTION("Constructor from free jobs")
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

        Permutation perm(jobs, mach_graph);

        REQUIRE(perm.m == 3);
        REQUIRE(perm.n == 2);
        REQUIRE(perm.level == 0);
        REQUIRE(perm.free_jobs.size() == 2);
    }
}

TEST_CASE("Permutation - push_job", "[permutation]")
{
    int M = 3;
    std::vector<std::vector<int>> prec = {{}, {0}, {1}};
    std::vector<std::vector<int>> succ = {{1}, {2}, {}};
    std::vector<int> topo_order = {0, 1, 2};
    std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};

    auto mach_graph =
        std::make_shared<MachineGraph>(M, prec, succ, topo_order, descendants);

    std::vector<std::vector<int>> p = {{3, 5, 2}, {2, 4, 3}, {1, 2, 1}};

    Permutation perm(p, mach_graph);

    SECTION("Push first job to sigma1 (even level)")
    {
        REQUIRE(perm.level == 0);
        REQUIRE(perm.free_jobs.size() == 3);
        REQUIRE(perm.sigma1.get_jobs().empty());

        perm.push_job(0);

        REQUIRE(perm.level == 1);
        REQUIRE(perm.free_jobs.size() == 2);
        REQUIRE(perm.sigma1.get_jobs().size() == 1);
        REQUIRE(perm.sigma1.get_jobs()[0]->j == 0);
        REQUIRE(perm.sigma2.get_jobs().empty());
    }

    SECTION("Push job to sigma2 (odd level)")
    {
        perm.push_job(0);  // Even level -> sigma1, removes free_jobs[0] (job 0)
        // free_jobs is now [job2, job1] after swap with last and pop

        REQUIRE(perm.level == 1);

        perm.push_job(0);  // Odd level -> sigma2, now free_jobs[0] is job 2

        REQUIRE(perm.level == 2);
        REQUIRE(perm.free_jobs.size() == 1);
        REQUIRE(perm.sigma1.get_jobs().size() == 1);
        REQUIRE(perm.sigma2.get_jobs().size() == 1);
        REQUIRE(perm.sigma1.get_jobs()[0]->j == 0);
        REQUIRE(perm.sigma2.get_jobs()[0]->j ==
                2);  // Was free_jobs[0] after first push
    }

    SECTION("Alternating push between sigma1 and sigma2")
    {
        // Initial: free_jobs = [job0, job1, job2]
        perm.push_job(0);  // job0 -> sigma1, free_jobs = [job2, job1]
        perm.push_job(1);  // job1 -> sigma2, free_jobs = [job2]
        perm.push_job(0);  // job2 -> sigma1, free_jobs = []

        REQUIRE(perm.level == 3);
        REQUIRE(perm.free_jobs.empty());
        REQUIRE(perm.sigma1.get_jobs().size() == 2);
        REQUIRE(perm.sigma2.get_jobs().size() == 1);
        REQUIRE(perm.sigma1.get_jobs()[0]->j == 0);
        REQUIRE(perm.sigma1.get_jobs()[1]->j == 2);
        REQUIRE(perm.sigma2.get_jobs()[0]->j == 1);
    }
}

TEST_CASE("Permutation - get_sequence", "[permutation]")
{
    int M = 3;
    std::vector<std::vector<int>> prec = {{}, {0}, {1}};
    std::vector<std::vector<int>> succ = {{1}, {2}, {}};
    std::vector<int> topo_order = {0, 1, 2};
    std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};

    auto mach_graph =
        std::make_shared<MachineGraph>(M, prec, succ, topo_order, descendants);

    std::vector<std::vector<int>> p = {{3, 5, 2}, {2, 4, 3}, {1, 2, 1}};

    Permutation perm(p, mach_graph);

    SECTION("Sequence with all free jobs")
    {
        std::vector<JobPtr> seq = perm.get_sequence();

        REQUIRE(seq.size() == 3);
        // sigma1 (empty) + free_jobs (3) + sigma2 (empty)
        REQUIRE(seq[0]->j == 0);
        REQUIRE(seq[1]->j == 1);
        REQUIRE(seq[2]->j == 2);
    }

    SECTION("Sequence with partial schedule")
    {
        // Initial: free_jobs = [job0, job1, job2]
        perm.push_job(0);  // job0 -> sigma1, free_jobs = [job2, job1]
        perm.push_job(1);  // job1 -> sigma2, free_jobs = [job2]

        std::vector<JobPtr> seq = perm.get_sequence();

        REQUIRE(seq.size() == 3);
        // sigma1 (job 0) + free_jobs (job 2) + sigma2 (job 1)
        REQUIRE(seq[0]->j == 0);
        REQUIRE(seq[1]->j == 2);
        REQUIRE(seq[2]->j == 1);
    }

    SECTION("Sequence with complete schedule")
    {
        // Push in specific order to get predictable result
        perm.push_job(2);  // job 2 -> sigma1, free_jobs = [job0, job1]
        perm.push_job(1);  // job 1 -> sigma2, free_jobs = [job0]
        perm.push_job(0);  // job 0 -> sigma1, free_jobs = []

        std::vector<JobPtr> seq = perm.get_sequence();

        REQUIRE(seq.size() == 3);
        // sigma1 (jobs 2, 0) + free_jobs (empty) + sigma2 (job 1)
        REQUIRE(seq[0]->j == 2);
        REQUIRE(seq[1]->j == 0);
        REQUIRE(seq[2]->j == 1);
    }
}

TEST_CASE("Permutation - is_feasible", "[permutation]")
{
    int M = 3;
    std::vector<std::vector<int>> prec = {{}, {0}, {1}};
    std::vector<std::vector<int>> succ = {{1}, {2}, {}};
    std::vector<int> topo_order = {0, 1, 2};
    std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};

    auto mach_graph =
        std::make_shared<MachineGraph>(M, prec, succ, topo_order, descendants);

    std::vector<std::vector<int>> p = {{3, 5, 2}, {2, 4, 3}};

    Permutation perm(p, mach_graph);

    SECTION("Not feasible with free jobs")
    {
        REQUIRE_FALSE(perm.is_feasible());
    }

    SECTION("Feasible when all jobs scheduled")
    {
        perm.push_job(0);
        perm.push_job(0);

        REQUIRE(perm.is_feasible());
    }
}

TEST_CASE("Permutation - lower bounds", "[permutation]")
{
    int M = 3;
    std::vector<std::vector<int>> prec = {{}, {0}, {1}};
    std::vector<std::vector<int>> succ = {{1}, {2}, {}};
    std::vector<int> topo_order = {0, 1, 2};
    std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};

    auto mach_graph =
        std::make_shared<MachineGraph>(M, prec, succ, topo_order, descendants);

    std::vector<std::vector<int>> p = {{3, 5, 2}, {2, 4, 3}};

    Permutation perm(p, mach_graph);

    SECTION("Single-machine lower bound with all free jobs")
    {
        int lb1m = perm.calc_lb_1m();

        // Should return lower_bound_1m since there are free jobs
        REQUIRE(lb1m > 0);
        REQUIRE(lb1m == perm.lower_bound_1m());
    }

    SECTION("Two-machine lower bound with all free jobs")
    {
        int lb2m = perm.calc_lb_2m();

        // Should return lower_bound_2m since there are free jobs
        REQUIRE(lb2m > 0);
        REQUIRE(lb2m == perm.lower_bound_2m());
    }

    SECTION("Full lower bound when all jobs scheduled")
    {
        perm.push_job(0);
        perm.push_job(0);

        int lb_full = perm.calc_lb_full();
        int lb1m = perm.calc_lb_1m();
        int lb2m = perm.calc_lb_2m();

        // All should return calc_lb_full since no free jobs
        REQUIRE(lb1m == lb_full);
        REQUIRE(lb2m == lb_full);
    }

    SECTION("Lower bounds are non-negative")
    {
        REQUIRE(perm.calc_lb_1m() >= 0);
        REQUIRE(perm.calc_lb_2m() >= 0);
        REQUIRE(perm.calc_lb_full() >= 0);
    }
}

TEST_CASE("Permutation - get_r and get_q", "[permutation]")
{
    int M = 3;
    std::vector<std::vector<int>> prec = {{}, {0}, {1}};
    std::vector<std::vector<int>> succ = {{1}, {2}, {}};
    std::vector<int> topo_order = {0, 1, 2};
    std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};

    auto mach_graph =
        std::make_shared<MachineGraph>(M, prec, succ, topo_order, descendants);

    std::vector<std::vector<int>> p = {{3, 5, 2}};

    Permutation perm(p, mach_graph);

    SECTION("Get release and tail times")
    {
        std::vector<int> r = perm.get_r();
        std::vector<int> q = perm.get_q();

        REQUIRE(r.size() == 3);
        REQUIRE(q.size() == 3);

        // For single job: r = [0, 3, 8], q = [7, 2, 0]
        REQUIRE(r[0] == 0);
        REQUIRE(r[1] == 3);
        REQUIRE(r[2] == 8);

        REQUIRE(q[0] == 7);
        REQUIRE(q[1] == 2);
        REQUIRE(q[2] == 0);
    }

    SECTION("Release and tail times after push_job")
    {
        perm.push_job(0);

        std::vector<int> r = perm.get_r();
        std::vector<int> q = perm.get_q();

        // After scheduling all jobs, cache might be updated
        REQUIRE(r.size() == 3);
        REQUIRE(q.size() == 3);
    }
}

TEST_CASE("Permutation - idle and total time", "[permutation]")
{
    int M = 3;
    std::vector<std::vector<int>> prec = {{}, {0}, {1}};
    std::vector<std::vector<int>> succ = {{1}, {2}, {}};
    std::vector<int> topo_order = {0, 1, 2};
    std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};

    auto mach_graph =
        std::make_shared<MachineGraph>(M, prec, succ, topo_order, descendants);

    std::vector<std::vector<int>> p = {{3, 5, 2}, {2, 4, 3}};

    Permutation perm(p, mach_graph);

    SECTION("Idle time with no scheduled jobs")
    {
        int idle = perm.calc_idle_time();

        // sigma1 and sigma2 are empty, so idle time should be 0
        REQUIRE(idle == 0);
    }

    SECTION("Total time with no scheduled jobs")
    {
        int total = perm.calc_tot_time();

        // sigma1 and sigma2 are empty
        REQUIRE(total == 0);
    }

    SECTION("Idle and total time after scheduling")
    {
        perm.push_job(0);
        perm.push_job(0);

        int idle = perm.calc_idle_time();
        int total = perm.calc_tot_time();

        REQUIRE(idle >= 0);
        REQUIRE(total > 0);
        REQUIRE(total >= idle);  // Total time >= idle time
    }
}

TEST_CASE("Permutation - two_mach_makespan function", "[permutation]")
{
    int M = 2;
    std::vector<std::vector<int>> prec = {{}, {0}};
    std::vector<std::vector<int>> succ = {{1}, {}};
    std::vector<int> topo_order = {0, 1};
    std::vector<std::vector<int>> descendants = {{1}, {}};

    MachineGraph mach_graph(M, prec, succ, topo_order, descendants);

    SECTION("Empty sequence")
    {
        std::vector<JobTimes*> empty_seq = {};
        int makespan = two_mach_makespan(empty_seq, 0, 0);

        REQUIRE(makespan == 0);
    }

    SECTION("Single job without latency")
    {
        Job job0(0, {5, 3}, mach_graph);
        JobTimes jt1(5 + 0, 3 + 0, 5, 3, 0, job0);
        std::vector<JobTimes*> seq = {&jt1};

        int makespan = two_mach_makespan(seq, 0, 0);

        // M1: 5, M2: max(5, 0) + 3 = 8
        REQUIRE(makespan == 8);
    }

    SECTION("Single job with latency")
    {
        Job job0(0, {5, 3}, mach_graph);
        job0.lat = {{0, 2}, {0, 0}};
        JobTimes jt1(5 + 2, 3 + 2, 5, 3, 2, job0);
        std::vector<JobTimes*> seq = {&jt1};

        int makespan = two_mach_makespan(seq, 0, 0);

        // M1: 5, M2: max(5+2, 0) + 3 = 10
        REQUIRE(makespan == 10);
    }

    SECTION("Multiple jobs without latency")
    {
        Job job0(0, {3, 2}, mach_graph);
        Job job1(1, {4, 5}, mach_graph);
        JobTimes jt1(3, 2, 3, 2, 0, job0);
        JobTimes jt2(4, 5, 4, 5, 0, job1);
        std::vector<JobTimes*> seq = {&jt1, &jt2};

        int makespan = two_mach_makespan(seq, 0, 0);

        // M1: 3+4=7, M2: max(3,0)+2=5, then max(7,5)+5=12
        REQUIRE(makespan == 12);
    }

    SECTION("Multiple jobs with latency and rho values")
    {
        Job job0(0, {3, 2}, mach_graph);
        Job job1(1, {4, 5}, mach_graph);
        job0.lat = {{0, 1}, {0, 0}};
        job1.lat = {{0, 2}, {0, 0}};
        JobTimes jt1(3 + 1, 2 + 1, 3, 2, 1, job0);
        JobTimes jt2(4 + 2, 5 + 2, 4, 5, 2, job1);
        std::vector<JobTimes*> seq = {&jt1, &jt2};

        int makespan = two_mach_makespan(seq, 2, 1);

        // M1: 3+4=7, rho1=2 -> M2 starts at 2
        // M2: max(3+1, 2) + 2 = max(4,2)+2 = 6
        //     max(7+2, 6) + 5 = max(9,6)+5 = 14
        // M1: 7+1=8
        // max(8, 14) = 14
        REQUIRE(makespan == 14);
    }
}

TEST_CASE("Permutation - copy constructor", "[permutation]")
{
    int M = 3;
    std::vector<std::vector<int>> prec = {{}, {0}, {1}};
    std::vector<std::vector<int>> succ = {{1}, {2}, {}};
    std::vector<int> topo_order = {0, 1, 2};
    std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};

    auto mach_graph =
        std::make_shared<MachineGraph>(M, prec, succ, topo_order, descendants);

    std::vector<std::vector<int>> p = {{3, 5, 2}, {2, 4, 3}};

    Permutation perm1(p, mach_graph);
    perm1.push_job(0);

    SECTION("Copy preserves state")
    {
        Permutation perm2(perm1);

        REQUIRE(perm2.m == perm1.m);
        REQUIRE(perm2.n == perm1.n);
        REQUIRE(perm2.level == perm1.level);
        REQUIRE(perm2.free_jobs.size() == perm1.free_jobs.size());
        REQUIRE(perm2.sigma1.get_jobs().size() ==
                perm1.sigma1.get_jobs().size());
    }

    SECTION("Copy is independent for modifications")
    {
        Permutation perm2(perm1);

        perm2.push_job(0);

        // perm2 modified, perm1 unchanged
        REQUIRE(perm2.level == perm1.level + 1);
        REQUIRE(perm2.free_jobs.size() == perm1.free_jobs.size() - 1);
    }
}

TEST_CASE("Permutation - assignment operator", "[permutation]")
{
    int M = 3;
    std::vector<std::vector<int>> prec = {{}, {0}, {1}};
    std::vector<std::vector<int>> succ = {{1}, {2}, {}};
    std::vector<int> topo_order = {0, 1, 2};
    std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};

    auto mach_graph =
        std::make_shared<MachineGraph>(M, prec, succ, topo_order, descendants);

    std::vector<std::vector<int>> p1 = {{3, 5, 2}, {2, 4, 3}};
    std::vector<std::vector<int>> p2 = {{1, 2, 1}};

    Permutation perm1(p1, mach_graph);
    Permutation perm2(p2, mach_graph);

    perm1.push_job(0);

    SECTION("Assignment copies state")
    {
        perm2 = perm1;

        REQUIRE(perm2.m == perm1.m);
        REQUIRE(perm2.n == perm1.n);
        REQUIRE(perm2.level == perm1.level);
        REQUIRE(perm2.free_jobs.size() == perm1.free_jobs.size());
    }
}

TEST_CASE("Permutation - compute_starts", "[permutation]")
{
    int M = 3;
    std::vector<std::vector<int>> prec = {{}, {0}, {1}};
    std::vector<std::vector<int>> succ = {{1}, {2}, {}};
    std::vector<int> topo_order = {0, 1, 2};
    std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};

    auto mach_graph =
        std::make_shared<MachineGraph>(M, prec, succ, topo_order, descendants);

    std::vector<std::vector<int>> p = {{3, 5, 2}};

    Permutation perm(p, mach_graph);
    perm.push_job(0);

    SECTION("Compute starts for complete schedule")
    {
        perm.compute_starts();

        std::vector<JobPtr> seq = perm.get_sequence();

        REQUIRE(seq.size() == 1);
        REQUIRE(seq[0]->s.size() == 3);

        // Start times should respect precedence
        REQUIRE(seq[0]->s[0] >= 0);
        REQUIRE(seq[0]->s[1] >= seq[0]->s[0] + seq[0]->p[0]);
        REQUIRE(seq[0]->s[2] >= seq[0]->s[1] + seq[0]->p[1]);
    }
}
