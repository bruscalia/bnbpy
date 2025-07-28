# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

import heapq

from bnbpy.cython.node cimport Node
from bnbpy.cython.priqueue cimport HeapPriQueue


cdef class DFSPriQueueFS(HeapPriQueue):
    cpdef void enqueue(self, Node node)
