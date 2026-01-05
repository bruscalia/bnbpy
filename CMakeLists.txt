# CMake configuration for C++ unit tests using Catch2
cmake_minimum_required(VERSION 3.14)
project(bnbpy_tests CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Include FetchContent module for downloading Catch2
include(FetchContent)

# Download and setup Catch2
FetchContent_Declare(
    Catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG v3.5.1  # Use a specific version
)
FetchContent_MakeAvailable(Catch2)

# Add the source directories
set(SRC_DIR ${CMAKE_CURRENT_SOURCE_DIR}/src/bnbprob/pafssp/cpp)
set(TEST_DIR ${CMAKE_CURRENT_SOURCE_DIR}/tests/cpp)

# Create test executables
add_executable(test_job ${TEST_DIR}/test_job.cpp ${SRC_DIR}/job.cpp)
add_executable(test_utils ${TEST_DIR}/test_utils.cpp ${SRC_DIR}/utils.cpp)
add_executable(test_sigma ${TEST_DIR}/test_sigma.cpp ${SRC_DIR}/sigma.cpp ${SRC_DIR}/job.cpp)
add_executable(test_job_times ${TEST_DIR}/test_job_times.cpp ${SRC_DIR}/job_times.cpp ${SRC_DIR}/job.cpp)
add_executable(test_two_mach ${TEST_DIR}/test_two_mach.cpp ${SRC_DIR}/two_mach.cpp ${SRC_DIR}/job.cpp ${SRC_DIR}/job_times.cpp)
add_executable(test_single_mach ${TEST_DIR}/test_single_mach.cpp ${SRC_DIR}/job.cpp)
add_executable(test_permutation ${TEST_DIR}/test_permutation.cpp ${SRC_DIR}/permutation.cpp ${SRC_DIR}/sigma.cpp ${SRC_DIR}/job.cpp ${SRC_DIR}/two_mach.cpp ${SRC_DIR}/job_times.cpp)

# Link against Catch2
target_link_libraries(test_job PRIVATE Catch2::Catch2WithMain)
target_link_libraries(test_utils PRIVATE Catch2::Catch2WithMain)
target_link_libraries(test_sigma PRIVATE Catch2::Catch2WithMain)
target_link_libraries(test_job_times PRIVATE Catch2::Catch2WithMain)
target_link_libraries(test_two_mach PRIVATE Catch2::Catch2WithMain)
target_link_libraries(test_single_mach PRIVATE Catch2::Catch2WithMain)
target_link_libraries(test_permutation PRIVATE Catch2::Catch2WithMain)

# Include directories
target_include_directories(test_job PRIVATE ${SRC_DIR})
target_include_directories(test_utils PRIVATE ${SRC_DIR})
target_include_directories(test_sigma PRIVATE ${SRC_DIR})
target_include_directories(test_job_times PRIVATE ${SRC_DIR})
target_include_directories(test_two_mach PRIVATE ${SRC_DIR})
target_include_directories(test_single_mach PRIVATE ${SRC_DIR})
target_include_directories(test_permutation PRIVATE ${SRC_DIR})

# Enable testing
enable_testing()
add_test(NAME JobTests COMMAND test_job)
add_test(NAME UtilsTests COMMAND test_utils)
add_test(NAME SigmaTests COMMAND test_sigma)
add_test(NAME JobTimesTests COMMAND test_job_times)
add_test(NAME TwoMachTests COMMAND test_two_mach)
add_test(NAME SingleMachTests COMMAND test_single_mach)
add_test(NAME PermutationTests COMMAND test_permutation)

# Optional: Add more verbose test output
list(APPEND CMAKE_CTEST_ARGUMENTS "--output-on-failure")
