# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False


cdef class Counter:
    def __init__(self):
        self.value = 0
