# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

import heapq

from bnbprob.slpfssp.cython.problem cimport PermFlowShop
from bnbpy.cython.node cimport Node
from bnbpy.cython.priqueue cimport HeapPriQueue, NodePriQueue


cdef class DFSPriQueueFS(HeapPriQueue):
    cpdef void enqueue(self, Node node):
        cdef:
            int idle_time
            PermFlowShop problem
        problem = node.problem
        idle_time = problem.calc_idle_time()
        heapq.heappush(
            self._queue,
            NodePriQueue((-node.level, node.lb, idle_time), node)
        )
