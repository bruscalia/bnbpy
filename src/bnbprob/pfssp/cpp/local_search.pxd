# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp.vector cimport vector

from bnbprob.pfssp.cpp.permutation cimport Permutation


cdef extern from "local_search.hpp":

    cdef Permutation local_search(Permutation &perm)
