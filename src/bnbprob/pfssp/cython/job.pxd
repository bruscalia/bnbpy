# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.memory cimport make_shared, shared_ptr


cdef extern from "job.h":

    cdef cppclass Job:
        int j
        int* p
        vector[int] r
        vector[int] q
        int** lat
        int slope
        int T

        # Declare the constructors
        # Default constructor
        Job()

        # Parameterized constructor
        Job(int j_, int* p_, const vector[int]& r_, const vector[int]& q_, int** lat_, int slope_, int T_)


ctypedef shared_ptr[Job] JobPtr
# ctypedef Job* JobPtr


cdef void fill_job(JobPtr& job, int& j, vector[int]& p) except *


cdef JobPtr start_job(int& j, vector[int]& p)


cdef JobPtr copy_job(shared_ptr[Job]& jobptr)


cdef void free_job(JobPtr& job)


cdef class PyJob:

    cdef:
        JobPtr job
        bool unsafe_alloc

    cpdef int get_T(self)

    cpdef int get_j(self)

    cpdef int get_p(self, int i)

    cpdef int get_r(self, int i)

    cpdef int get_lat(self, int i, int j)
