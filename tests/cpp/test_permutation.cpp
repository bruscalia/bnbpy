#include <type_traits>

#include "catch2/catch_test_macros.hpp"
#include "instance_data.hpp"
#include "job.hpp"
#include "mach_graph.hpp"
#include "permutation.hpp"
#include "sigma.hpp"

// Rule of zero: copies share the instance, moves are cheap
static_assert(std::is_copy_constructible_v<Permutation>);
static_assert(std::is_nothrow_move_constructible_v<Permutation>);
static_assert(std::is_nothrow_move_assignable_v<Permutation>);

namespace
{
// Sequential machine graph 0 -> 1 -> 2
MachineGraph chain3()
{
    std::vector<std::vector<int>> prec = {{}, {0}, {1}};
    std::vector<std::vector<int>> succ = {{1}, {2}, {}};
    std::vector<int> topo_order = {0, 1, 2};
    std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};
    return MachineGraph(3, prec, succ, topo_order, descendants);
}
}  // namespace

TEST_CASE("Permutation - constructors", "[permutation]")
{
    SECTION("Default constructor")
    {
        Permutation perm;

        REQUIRE(perm.m == 0);
        REQUIRE(perm.n == 0);
        REQUIRE(perm.level == 0);
        REQUIRE(perm.free_jobs.empty());
        REQUIRE(perm.instance == nullptr);
    }

    SECTION("Root constructor")
    {
        InstanceData inst({{3, 5, 2}, {2, 4, 3}}, chain3());

        Permutation perm(&inst);

        REQUIRE(perm.m == 3);
        REQUIRE(perm.n == 2);
        REQUIRE(perm.level == 0);
        REQUIRE(perm.free_jobs.size() == 2);
        REQUIRE(perm.sigma1.get_jobs().empty());
        REQUIRE(perm.sigma2.get_jobs().empty());
        REQUIRE(perm.get_instance() == &inst);
        REQUIRE(&perm.get_mach_graph() == &inst.get_mach_graph());
        REQUIRE(perm.sigma1.mach_graph == &inst.get_mach_graph());
        REQUIRE(perm.sigma2.mach_graph == &inst.get_mach_graph());
    }

    SECTION("Constructor from free jobs")
    {
        InstanceData inst({{3, 5, 2}, {2, 4, 3}}, chain3());

        Permutation perm(&inst, inst.get_jobs());

        REQUIRE(perm.m == 3);
        REQUIRE(perm.n == 2);
        REQUIRE(perm.level == 0);
        REQUIRE(perm.free_jobs.size() == 2);
    }

    SECTION("Constructor from a subset of free jobs keeps n of instance")
    {
        InstanceData inst({{3, 5, 2}, {2, 4, 3}, {1, 2, 1}}, chain3());

        // Job 2 only: indexes scheduled_jobs by j = 2, which must be in bounds
        Permutation perm(&inst, {inst.get_jobs()[2]});

        REQUIRE(perm.n == 3);
        REQUIRE(perm.free_jobs.size() == 1);
        perm.push_job(0);
        REQUIRE(perm.is_feasible());
        REQUIRE(perm.calc_lb_full() == 4);
    }

    SECTION("Full-state constructor marks prescheduled jobs")
    {
        InstanceData inst({{3, 5, 2}, {2, 4, 3}, {1, 2, 1}}, chain3());
        const std::vector<JobPtr> &jobs = inst.get_jobs();
        const MachineGraph *mg = &inst.get_mach_graph();

        Sigma s1(3, mg);
        s1.job_to_bottom(jobs[0]);
        Sigma s2(3, mg);
        s2.job_to_top(jobs[2]);

        Permutation perm(&inst, 2, s1, {jobs[1]}, s2);

        REQUIRE(perm.level == 2);
        REQUIRE(perm.n == 3);
        REQUIRE(perm.free_jobs.size() == 1);
        // Two-machine bounds only consider the unscheduled job 1 (2, 4, 3)
        REQUIRE(perm.two_mach_bound(0, 1, 0, 0) == 6);
        REQUIRE(perm.two_mach_bound(0, 2, 0, 0) == 9);
    }
}

TEST_CASE("Permutation - push_job", "[permutation]")
{
    InstanceData inst({{3, 5, 2}, {2, 4, 3}, {1, 2, 1}}, chain3());

    Permutation perm(&inst);

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
    InstanceData inst({{3, 5, 2}, {2, 4, 3}, {1, 2, 1}}, chain3());

    Permutation perm(&inst);

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
    InstanceData inst({{3, 5, 2}, {2, 4, 3}}, chain3());

    Permutation perm(&inst);

    SECTION("Not feasible with free jobs")
    {
        REQUIRE_FALSE(perm.is_feasible());
    }

    SECTION("Feasible when all jobs scheduled")
    {
        perm.push_job(0);
        perm.push_job(0);

        const Permutation &cperm = perm;  // is_feasible is const
        REQUIRE(cperm.is_feasible());
        REQUIRE(cperm.is_feasible());
    }
}

TEST_CASE("Permutation - lower bounds", "[permutation]")
{
    InstanceData inst({{3, 5, 2}, {2, 4, 3}}, chain3());

    Permutation perm(&inst);

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
    InstanceData inst({{3, 5, 2}}, chain3());

    Permutation perm(&inst);

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
    InstanceData inst({{3, 5, 2}, {2, 4, 3}}, chain3());

    Permutation perm(&inst);

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

TEST_CASE("Permutation - two_mach_bound", "[permutation]")
{
    // Sequential machine graph 0 -> 1
    std::vector<std::vector<int>> prec = {{}, {0}};
    std::vector<std::vector<int>> succ = {{1}, {}};
    std::vector<int> topo_order = {0, 1};
    std::vector<std::vector<int>> descendants = {{1}, {}};
    MachineGraph chain2(2, prec, succ, topo_order, descendants);

    SECTION("No free jobs: only heads and tails")
    {
        InstanceData inst({{5, 3}}, chain2);
        Permutation perm(&inst);
        perm.push_job(0);

        REQUIRE(perm.two_mach_bound(0, 1, 0, 0) == 0);
        REQUIRE(perm.two_mach_bound(0, 1, 4, 6) == 6);
    }

    SECTION("Single job without latency")
    {
        InstanceData inst({{5, 3}}, chain2);
        Permutation perm(&inst);

        // M1: 5, M2: max(5, 0) + 3 = 8
        REQUIRE(perm.two_mach_bound(0, 1, 0, 0) == 8);
    }

    SECTION("Single job with latency")
    {
        InstanceData inst({{3, 4, 2}}, chain3());
        Permutation perm(&inst);

        // Pair (0, 2): lat = p[1] = 4
        // M1: 3, M2: max(3 + 4, 0) + 2 = 9
        REQUIRE(perm.two_mach_bound(0, 2, 0, 0) == 9);
    }

    SECTION("Multiple jobs in Johnson order with rho values")
    {
        // Job 0 (3, 2): t1 > t2 -> second set
        // Job 1 (4, 5): t1 <= t2 -> first set
        // Johnson order: [job 1, job 0]
        InstanceData inst({{3, 2}, {4, 5}}, chain2);
        Permutation perm(&inst);

        // M1: 4, M2: 9; M1: 7, M2: max(7, 9) + 2 = 11
        REQUIRE(perm.two_mach_bound(0, 1, 0, 0) == 11);
        // rho1 = 10: M2: max(4, 10) + 5 = 15; max(7, 15) + 2 = 17
        REQUIRE(perm.two_mach_bound(0, 1, 10, 0) == 17);
        // rho2 = 12: M1: 7 + 12 = 19 > M2: 11
        REQUIRE(perm.two_mach_bound(0, 1, 0, 12) == 19);
    }

    SECTION("Scheduled jobs are skipped")
    {
        InstanceData inst({{3, 2}, {4, 5}}, chain2);
        Permutation perm(&inst);
        perm.push_job(0);  // job 0 -> sigma1

        // Only job 1: M1: 4, M2: max(4, 0) + 5 = 9
        REQUIRE(perm.two_mach_bound(0, 1, 0, 0) == 9);
    }
}

TEST_CASE("Permutation - copy constructor", "[permutation]")
{
    InstanceData inst({{3, 5, 2}, {2, 4, 3}}, chain3());

    Permutation perm1(&inst);
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
        REQUIRE(perm2.instance == perm1.instance);
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
    InstanceData inst1({{3, 5, 2}, {2, 4, 3}}, chain3());
    InstanceData inst2({{1, 2, 1}}, chain3());

    Permutation perm1(&inst1);
    Permutation perm2(&inst2);

    perm1.push_job(0);

    SECTION("Assignment copies state")
    {
        perm2 = perm1;

        REQUIRE(perm2.m == perm1.m);
        REQUIRE(perm2.n == perm1.n);
        REQUIRE(perm2.level == perm1.level);
        REQUIRE(perm2.free_jobs.size() == perm1.free_jobs.size());
        REQUIRE(perm2.instance == &inst1);
    }
}

TEST_CASE("Permutation - compute_starts", "[permutation]")
{
    SECTION("Single job respects machine precedence")
    {
        InstanceData inst({{3, 5, 2}}, chain3());
        Permutation perm(&inst);
        perm.push_job(0);

        std::vector<std::vector<int>> starts = perm.compute_starts();

        REQUIRE(starts.size() == 1);
        REQUIRE(starts[0] == std::vector<int>{0, 3, 8});
    }

    SECTION("Complete schedule: exact starts aligned with get_sequence")
    {
        InstanceData inst({{3, 5, 2}, {2, 4, 3}, {1, 2, 1}}, chain3());
        Permutation perm(&inst);
        perm.push_job(2);  // job 2 -> sigma1
        perm.push_job(1);  // job 1 -> sigma2
        perm.push_job(0);  // job 0 -> sigma1

        const Permutation &cperm = perm;  // compute_starts is const
        std::vector<JobPtr> seq = cperm.get_sequence();
        std::vector<std::vector<int>> starts = cperm.compute_starts();

        // Sequence [2, 0, 1]
        // job 2 (1, 2, 1): starts (0, 1, 3)
        // job 0 (3, 5, 2): starts (1, 4, 9)
        // job 1 (2, 4, 3): starts (4, 9, 13) -> makespan 16
        REQUIRE(seq[0]->j == 2);
        REQUIRE(seq[1]->j == 0);
        REQUIRE(seq[2]->j == 1);
        REQUIRE(starts ==
                std::vector<std::vector<int>>{{0, 1, 3}, {1, 4, 9}, {4, 9, 13}});
        REQUIRE(starts[2][2] + seq[2]->p[2] == perm.calc_lb_full());

        // Pure function: same result when called again
        REQUIRE(cperm.compute_starts() == starts);
    }

    SECTION("Partial schedule follows sigma1 + free jobs + sigma2")
    {
        InstanceData inst({{3, 5, 2}, {2, 4, 3}, {1, 2, 1}}, chain3());
        Permutation perm(&inst);

        // Sequence [0, 1, 2], all free
        std::vector<std::vector<int>> starts = perm.compute_starts();

        REQUIRE(starts ==
                std::vector<std::vector<int>>{{0, 3, 8}, {3, 8, 12}, {5, 12, 15}});
    }

    SECTION("Default permutation has no starts")
    {
        Permutation perm;

        REQUIRE(perm.compute_starts().empty());
    }
}
