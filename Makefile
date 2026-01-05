# Makefile for building and running C++ tests using CMake

BUILD_DIR = build
TARGET = $(BUILD_DIR)/test_job

# Default target: configure and build
all: $(TARGET)

# Configure CMake (only if build directory doesn't exist or CMake files are missing)
$(BUILD_DIR)/Makefile:
	cmake -B $(BUILD_DIR) -S .

# Build the test executable
$(TARGET): $(BUILD_DIR)/Makefile
	cmake --build $(BUILD_DIR)

# Run all tests from root directory
test: $(TARGET)
	@echo "Running all C++ tests..."
	@$(BUILD_DIR)/test_job
	@$(BUILD_DIR)/test_utils
	@$(BUILD_DIR)/test_sigma
	@$(BUILD_DIR)/test_job_times
	@$(BUILD_DIR)/test_two_mach
	@$(BUILD_DIR)/test_single_mach
	@$(BUILD_DIR)/test_permutation

# Run tests with verbose output
test-verbose: $(TARGET)
	@$(BUILD_DIR)/test_job -s
	@$(BUILD_DIR)/test_utils -s
	@$(BUILD_DIR)/test_sigma -s
	@$(BUILD_DIR)/test_job_times -s
	@$(BUILD_DIR)/test_two_mach -s
	@$(BUILD_DIR)/test_single_mach -s
	@$(BUILD_DIR)/test_permutation -s

# Run specific test case (usage: make test-case CASE="[job]")
test-case: $(TARGET)
	@$(BUILD_DIR)/test_job $(CASE)
	@$(BUILD_DIR)/test_utils $(CASE)
	@$(BUILD_DIR)/test_sigma $(CASE)
	@$(BUILD_DIR)/test_job_times $(CASE)
	@$(BUILD_DIR)/test_two_mach $(CASE)
	@$(BUILD_DIR)/test_single_mach $(CASE)
	@$(BUILD_DIR)/test_permutation $(CASE)

# Run tests using CTest
ctest: $(TARGET)
	cd $(BUILD_DIR) && ctest --output-on-failure

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR)

# Rebuild everything
rebuild: clean all

# Reconfigure CMake
reconfigure:
	rm -rf $(BUILD_DIR)
	cmake -B $(BUILD_DIR) -S .

.PHONY: all test test-verbose test-case ctest clean rebuild reconfigure
