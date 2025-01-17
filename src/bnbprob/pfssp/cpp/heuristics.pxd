# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.memory cimport shared_ptr

from bnbprob.pfssp.cpp.job cimport JobPtr
from bnbprob.pfssp.cpp.permutation cimport Permutation
from bnbprob.pfssp.cpp.sigma cimport Sigma


cdef extern from "quick_constructive.hpp":

    cdef Permutation quick_constructive(std::vector<JobPtr> &jobs)


cdef extern from "neh.hpp":

    cdef Permutation neh_constructive(std::vector<JobPtr> &jobs)


cdef extern from "local_search.hpp":

    cdef Permutation neh_constructive(Permutation &perm)
