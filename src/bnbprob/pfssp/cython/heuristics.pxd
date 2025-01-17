# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.algorithm cimport sort
from libcpp.vector cimport vector

from cython.operator cimport dereference as deref

from bnbprob.pfssp.cpp.job cimport JobPtr
from bnbprob.pfssp.cpp.permutation cimport Permutation
from bnbprob.pfssp.cpp.sigma cimport Sigma

cdef:
    int LARGE_INT = 10000000


cdef Permutation quick_constructive(vector[JobPtr]& jobs) except *


cdef Permutation neh_constructive(vector[JobPtr]& jobs) except *


cdef Permutation local_search(Permutation perm) except *


cdef void recompute_r0(vector[JobPtr]& jobs)