# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False


cdef class Counter:
    cdef:
        int value

    cdef inline int next(Counter self):
        self.value += 1
        return self.get_value()

    cpdef int get_value(Counter self)
