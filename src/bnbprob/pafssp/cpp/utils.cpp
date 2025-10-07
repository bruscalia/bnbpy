#include "utils.hpp"

#include <algorithm>
#include <limits>
#include <vector>

#include "job.hpp"

int SMALL = -1000000;

int get_max_value(const int *&ptr, int &m)
{
    // Check if the pointer is null or the size is zero
    if (!ptr || m <= 0)
    {
        return SMALL;  // Return the smallest integer as an error value
    }

    int max_val = ptr[0];  // Initialize with the first element
    for (int i = 1; i < m; ++i)
    {
        if (ptr[i] > max_val)
        {
            max_val = ptr[i];
        }
    }
    return max_val;
}

int get_max_value(const std::vector<int> &vec)
{
    // Check if the pointer is null or the size is zero
    int max_val = *std::max_element(vec.begin(), vec.end());
    return max_val;
}

int get_max_value(const std::vector<int> &v1, const std::vector<int> &v2)
{
    int min_size = std::min(v1.size(), v2.size());
    int max_val = SMALL;
    for (int i = 0; i < min_size; ++i)
    {
        int val = v1[i] + v2[i];
        if (val > max_val)
        {
            max_val = val;
        }
    }
    return max_val;
}
