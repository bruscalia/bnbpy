# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp.vector cimport vector

from bnbprob.pfssp.cpp.job cimport JobPtr
from bnbprob.pfssp.cpp.permutation cimport Permutation


cdef extern from "quick_constructive.hpp":

    cdef Permutation quick_constructive(vector[JobPtr] &jobs)
