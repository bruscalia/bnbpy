# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp.vector cimport vector
from libcpp.memory cimport shared_ptr

from bnbprob.pfssp.cpp.job cimport Job
from bnbprob.pfssp.cpp.permutation cimport Permutation


cdef extern from "quick_constructive.hpp":

    cdef Permutation quick_constructive(vector[shared_ptr[Job]] &jobs)
