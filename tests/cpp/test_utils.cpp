#include "catch2/catch_test_macros.hpp"
#include "utils.hpp"

TEST_CASE("Utils - get_max_value for vector", "[utils]")
{
    SECTION("Single element vector")
    {
        std::vector<int> vec = {42};
        REQUIRE(get_max_value(vec) == 42);
    }

    SECTION("Multiple elements")
    {
        std::vector<int> vec = {3, 7, 2, 9, 1};
        REQUIRE(get_max_value(vec) == 9);
    }

    SECTION("Negative values")
    {
        std::vector<int> vec = {-5, -2, -10, -1};
        REQUIRE(get_max_value(vec) == -1);
    }

    SECTION("Mixed positive and negative")
    {
        std::vector<int> vec = {-5, 10, -3, 0, 7};
        REQUIRE(get_max_value(vec) == 10);
    }
}

TEST_CASE("Utils - get_max_value for pointer array", "[utils]")
{
    SECTION("Single element array")
    {
        int arr[] = {42};
        const int* ptr = arr;
        int size = 1;
        REQUIRE(get_max_value(ptr, size) == 42);
    }

    SECTION("Multiple elements")
    {
        int arr[] = {3, 7, 2, 9, 1};
        const int* ptr = arr;
        int size = 5;
        REQUIRE(get_max_value(ptr, size) == 9);
    }

    SECTION("Null pointer returns SMALL value")
    {
        const int* ptr = nullptr;
        int size = 5;
        REQUIRE(get_max_value(ptr, size) == -1000000);
    }

    SECTION("Zero size returns SMALL value")
    {
        int arr[] = {1, 2, 3};
        const int* ptr = arr;
        int size = 0;
        REQUIRE(get_max_value(ptr, size) == -1000000);
    }

    SECTION("Negative size returns SMALL value")
    {
        int arr[] = {1, 2, 3};
        const int* ptr = arr;
        int size = -1;
        REQUIRE(get_max_value(ptr, size) == -1000000);
    }
}

TEST_CASE("Utils - get_max_value for pairwise sum", "[utils]")
{
    SECTION("Equal size vectors")
    {
        std::vector<int> v1 = {1, 2, 3};
        std::vector<int> v2 = {4, 5, 6};
        // Max of (1+4=5, 2+5=7, 3+6=9) = 9
        REQUIRE(get_max_value(v1, v2) == 9);
    }

    SECTION("First vector longer")
    {
        std::vector<int> v1 = {1, 2, 3, 100};
        std::vector<int> v2 = {4, 5, 6};
        // Only considers min size = 3
        REQUIRE(get_max_value(v1, v2) == 9);
    }

    SECTION("Second vector longer")
    {
        std::vector<int> v1 = {1, 2, 3};
        std::vector<int> v2 = {4, 5, 6, 100};
        // Only considers min size = 3
        REQUIRE(get_max_value(v1, v2) == 9);
    }

    SECTION("Negative sums")
    {
        std::vector<int> v1 = {-10, -5, -2};
        std::vector<int> v2 = {-1, -3, -4};
        // Max of (-11, -8, -6) = -6
        REQUIRE(get_max_value(v1, v2) == -6);
    }

    SECTION("Mixed positive and negative")
    {
        std::vector<int> v1 = {5, -3, 10};
        std::vector<int> v2 = {-2, 8, -5};
        // Sums: (3, 5, 5), max = 5
        REQUIRE(get_max_value(v1, v2) == 5);
    }

    SECTION("Empty vectors")
    {
        std::vector<int> v1 = {};
        std::vector<int> v2 = {};
        // Should return SMALL since no elements to compare
        REQUIRE(get_max_value(v1, v2) == -1000000);
    }

    SECTION("One empty vector")
    {
        std::vector<int> v1 = {1, 2, 3};
        std::vector<int> v2 = {};
        // Min size is 0
        REQUIRE(get_max_value(v1, v2) == -1000000);
    }
}
