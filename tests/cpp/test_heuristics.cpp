#include <algorithm>
#include <random>
#include <vector>

#include "catch2/catch_test_macros.hpp"
#include "iga.hpp"
#include "instance_data.hpp"
#include "job.hpp"
#include "mach_graph.hpp"
#include "neh.hpp"
#include "permutation.hpp"

namespace
{
// Sequential graph 0 -> 1 -> 2
MachineGraph chain3()
{
    std::vector<std::vector<int>> prec = {{}, {0}, {1}};
    std::vector<std::vector<int>> succ = {{1}, {2}, {}};
    std::vector<int> topo_order = {0, 1, 2};
    std::vector<std::vector<int>> descendants = {{1, 2}, {2}, {}};
    return MachineGraph(3, prec, succ, topo_order, descendants);
}

std::vector<std::vector<int>> processing_times(int n)
{
    std::vector<std::vector<int>> all = {
        {3, 5, 2}, {2, 4, 3}, {6, 1, 2}, {4, 4, 4}, {1, 7, 3}};
    return std::vector<std::vector<int>>(all.begin(), all.begin() + n);
}

// Every job of the instance appears exactly once in a complete sequence
void require_complete(const Permutation &perm, int n)
{
    REQUIRE(perm.is_feasible());
    std::vector<int> ids;
    for (JobPtr job : perm.get_sequence())
    {
        ids.push_back(job->j);
    }
    std::sort(ids.begin(), ids.end());
    std::vector<int> expected(n);
    for (int j = 0; j < n; ++j)
    {
        expected[j] = j;
    }
    REQUIRE(ids == expected);
}
}  // namespace

TEST_CASE("NEH - fewer than two jobs", "[neh]")
{
    InstanceData inst(processing_times(1), chain3());
    std::vector<JobPtr> jobs = inst.get_jobs();

    Permutation perm = neh_initialization(jobs, inst);

    require_complete(perm, 1);
    REQUIRE(perm.calc_lb_full() == 3 + 5 + 2);
}

TEST_CASE("NEH - complete sequences", "[neh]")
{
    for (int n = 2; n <= 5; ++n)
    {
        InstanceData inst(processing_times(n), chain3());
        std::vector<JobPtr> jobs = inst.get_jobs();
        require_complete(neh_initialization(jobs, inst), n);
    }
}

TEST_CASE("IGA - destruction size larger than the number of jobs", "[iga]")
{
    for (int n = 1; n <= 5; ++n)
    {
        InstanceData inst(processing_times(n), chain3());
        std::vector<JobPtr> jobs = inst.get_jobs();
        Permutation start = neh_initialization(jobs, inst);
        std::vector<JobPtr> seq = start.get_sequence();

        Permutation perm = iga(seq, inst, 10, 5, 7);

        require_complete(perm, n);
        // Never worse than the starting sequence
        REQUIRE(perm.calc_lb_full() <= start.calc_lb_full());
    }
}

TEST_CASE("IGA - destruction", "[iga]")
{
    InstanceData inst(processing_times(5), chain3());
    std::vector<JobPtr> jobs = inst.get_jobs();
    std::mt19937 generator(3);

    SECTION("Destruction size is clamped to the number of jobs")
    {
        IGADestruction result = iga_destruction(jobs, 8, generator);
        REQUIRE(result.sequence.empty());
        REQUIRE(result.free_jobs.size() == jobs.size());
    }

    SECTION("Removed and kept jobs partition the input")
    {
        IGADestruction result = iga_destruction(jobs, 2, generator);
        REQUIRE(result.free_jobs.size() == 2);
        REQUIRE(result.sequence.size() == jobs.size() - 2);
    }

    SECTION("The generator is advanced by each destruction")
    {
        std::mt19937 before = generator;
        iga_destruction(jobs, 2, generator);
        REQUIRE_FALSE(generator == before);
    }
}
