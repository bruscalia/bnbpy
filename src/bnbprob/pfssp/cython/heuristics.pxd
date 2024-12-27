# distutils: language = c++
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from bnbprob.pfssp.cython.job cimport Job
from bnbprob.pfssp.cython.permutation cimport Permutation


cpdef Permutation quick_constructive(list[Job] jobs)


cpdef Permutation neh_constructive(list[Job] jobs)


cpdef Permutation local_search(Permutation perm)


cdef void recompute_r0(list[Job] jobs)
