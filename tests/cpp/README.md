# C++ Unit Tests for bnbpy

This directory contains C++ unit tests using the Catch2 testing framework.

## Prerequisites

### Option 1: Using CMake (Recommended)
CMake will automatically download and configure Catch2 for you.

- CMake 3.14 or higher
- A C++17 compatible compiler (g++, clang++, etc.)
- Git (for fetching Catch2)

### Option 2: Using Makefile
You need to have Catch2 installed on your system.

**Ubuntu/Debian:**
```bash
sudo apt-get install catch2
```

**macOS:**
```bash
brew install catch2
```

**Fedora:**
```bash
sudo dnf install catch2-devel
```

**From source:**
```bash
git clone https://github.com/catchorg/Catch2.git
cd Catch2
cmake -Bbuild -H. -DBUILD_TESTING=OFF
sudo cmake --build build/ --target install
```

## Building and Running Tests

### Using CMake (Recommended for Cython context)

```bash
# Navigate to the test directory
cd tests/cpp

# Create build directory
mkdir -p build
cd build

# Configure and build
cmake ..
cmake --build .

# Run tests
ctest --output-on-failure

# Or run the executable directly for more control
./test_job

# Run with verbose output
./test_job -s

# Run specific test cases
./test_job "[job]"
./test_job "[slope]"
```

### Using Makefile (Simpler, requires system Catch2)

```bash
# Navigate to the test directory
cd tests/cpp

# Build tests
make

# Run tests
make test

# Run with verbose output
make test-verbose

# Run specific test case
make test-case

# Clean build artifacts
make clean
```

### Manual Compilation

If you prefer to compile manually:

```bash
g++ -std=c++17 -Wall -Wextra \
    -I../../src/bnbprob/pafssp/cpp \
    -o test_job \
    test_job.cpp ../../src/bnbprob/pafssp/cpp/job.cpp

./test_job
```

## Test Structure

The tests use Catch2's BDD-style syntax with `TEST_CASE` and `SECTION` blocks:

- **TEST_CASE**: Groups related tests together
- **SECTION**: Subdivides test cases into isolated scenarios
- **REQUIRE**: Assert that a condition is true (fails test if false)

## Adding New Tests

To add tests for other classes:

1. Create a new test file (e.g., `test_mach_graph.cpp`)
2. Include Catch2 headers (but don't define CATCH_CONFIG_MAIN again)
3. Add your TEST_CASE blocks
4. Update CMakeLists.txt to add the new test executable
5. Update Makefile if using that approach

Example for adding machine graph tests:

```cpp
// test_mach_graph.cpp
#include "catch2/catch_test_macros.hpp"
#include "../../src/bnbprob/pafssp/cpp/mach_graph.hpp"

TEST_CASE("MachineGraph basic operations", "[mach_graph]")
{
    // Your tests here
}
```

Then update CMakeLists.txt:
```cmake
add_executable(test_mach_graph test_mach_graph.cpp)
target_link_libraries(test_mach_graph PRIVATE Catch2::Catch2WithMain)
target_include_directories(test_mach_graph PRIVATE ${SRC_DIR})
add_test(NAME MachGraphTests COMMAND test_mach_graph)
```

## Useful Catch2 Command-Line Options

- `-s` or `--success`: Show successful tests
- `-b` or `--break`: Break into debugger on failure
- `--list-tests`: List all test cases
- `--list-tags`: List all tags
- `[tag]`: Run only tests with specific tag
- `-#` or `--filenames-as-tags`: Use filename as tag

## Integration with Cython Build

Since you're using Cython, the C++ tests are independent of the Python build process. You can:

1. Run tests during development without rebuilding the Python extension
2. Add a test step to your CI/CD pipeline
3. Use the same C++ source files that Cython wraps

The tests compile the C++ code directly without going through Cython, which makes debugging easier and faster during C++ development.

## Troubleshooting

**Issue**: `catch2/catch_test_macros.hpp: No such file or directory`
- **Solution**: Install Catch2 or use CMake which downloads it automatically

**Issue**: `undefined reference to MachineGraph constructor`
- **Solution**: Make sure all necessary .cpp files are included in compilation

**Issue**: Tests compile but fail
- **Solution**: Check the test logic and ensure the MachineGraph and Job implementations are correct

## Example Output

Successful test run:
```
===============================================================================
All tests passed (42 assertions in 7 test cases)
```

Failed test run:
```
test_job.cpp:25: FAILED:
  REQUIRE( job.r[1] == 3 )
with expansion:
  5 == 3
```
