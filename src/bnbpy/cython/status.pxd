# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

cpdef enum OptStatus:
    NO_SOLUTION = 0
    RELAXATION = 1
    OPTIMAL = 2
    FEASIBLE = 3
    INFEASIBLE = 4
    FATHOM = 5
    ERROR = 6
    OTHER = 7
