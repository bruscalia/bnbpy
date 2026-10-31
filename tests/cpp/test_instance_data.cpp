#include <stdexcept>
#include <type_traits>

#include "catch2/catch_test_macros.hpp"
#include "instance_data.hpp"
#include "job.hpp"
#include "mach_graph.hpp"
#include "two_mach.hpp"

// Raw pointers into InstanceData must stay valid: no copies, no moves
static_assert(!std::is_copy_constructible_v<InstanceData>);
static_assert(!std::is_copy_assignable_v<InstanceData>);
static_assert(!std::is_move_constructible_v<InstanceData>);
static_assert(!std::is_move_assignable_v<InstanceData>);

namespace
{
// Assembly graph: 0 -> 2, 1 -> 2, 2 -> 3
MachineGraph assembly4()
{
    std::vector<std::vector<int>> prec = {{}, {}, {0, 1}, {2}};
    std::vector<std::vector<int>> succ = {{2}, {2}, {3}, {}};
    std::vector<int> topo_order = {0, 1, 2, 3};
    std::vector<std::vector<int>> descendants = {{2, 3}, {2, 3}, {3}, {}};
    return MachineGraph(4, prec, succ, topo_order, descendants);
}
}  // namespace

TEST_CASE("InstanceData - construction", "[instance_data]")
{
    std::vector<std::vector<int>> p = {
        {3, 5, 2, 4}, {2, 4, 3, 1}, {6, 1, 2, 2}};
    MachineGraph graph = assembly4();
    InstanceData inst(p, graph);

    SECTION("Sizes")
    {
        REQUIRE(inst.get_n() == 3);
        REQUIRE(inst.get_m() == 4);
        REQUIRE(inst.get_jobs().size() == 3);
        REQUIRE(inst.get_mach_graph().get_M() == 4);
        REQUIRE(inst.get_mach_graph().get_topo_order() ==
                graph.get_topo_order());
    }

    SECTION("Job pointers are stable and indexed by job id")
    {
        const std::vector<JobPtr> &jobs = inst.get_jobs();
        for (int j = 0; j < inst.get_n(); ++j)
        {
            REQUIRE(jobs[j]->j == j);
            REQUIRE(jobs[j]->p == p[j]);
        }
        // Same pointers on every call
        REQUIRE(inst.get_jobs()[1] == jobs[1]);
    }

    SECTION("Jobs match standalone Job construction")
    {
        for (int j = 0; j < inst.get_n(); ++j)
        {
            Job ref(j, p[j], graph);
            const Job &job = *inst.get_jobs()[j];
            REQUIRE(job.r == ref.r);
            REQUIRE(job.q == ref.q);
            REQUIRE(job.lat == ref.lat);
        }
    }

    SECTION("Two-machine cache matches a standalone TwoMach")
    {
        std::vector<Job> ref_jobs;
        for (int j = 0; j < inst.get_n(); ++j)
        {
            ref_jobs.emplace_back(j, p[j], graph);
        }
        std::vector<JobPtr> ref_ptrs;
        for (const Job &job : ref_jobs)
        {
            ref_ptrs.push_back(&job);
        }
        TwoMach ref(graph, ref_ptrs);

        const TwoMach &cache = inst.get_two_mach();
        for (int m1 = 0; m1 < inst.get_m(); ++m1)
        {
            for (int m2 : graph.get_descendants()[m1])
            {
                const JobTimes1D &seq = cache.get_seq(m1, m2);
                const JobTimes1D &ref_seq = ref.get_seq(m1, m2);
                REQUIRE(seq.size() == ref_seq.size());
                for (size_t k = 0; k < seq.size(); ++k)
                {
                    REQUIRE(seq[k].j == ref_seq[k].j);
                    REQUIRE(seq[k].t1 == ref_seq[k].t1);
                    REQUIRE(seq[k].t2 == ref_seq[k].t2);
                    REQUIRE(seq[k].lat == ref_seq[k].lat);
                }
            }
        }
    }

    SECTION("Missing machine pair is an error, not an insertion")
    {
        // (3, 0) is not a descendant pair
        REQUIRE_THROWS_AS(inst.get_two_mach().get_seq(3, 0), std::out_of_range);
    }
}

TEST_CASE("InstanceData - invalid processing times", "[instance_data]")
{
    // Row 1 has 3 processing times for a 4-machine graph
    std::vector<std::vector<int>> p = {{3, 5, 2, 4}, {2, 4, 3}};
    REQUIRE_THROWS_AS(InstanceData(p, assembly4()), std::invalid_argument);
}
