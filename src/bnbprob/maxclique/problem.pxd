# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

from libcpp cimport bool

from bnbprob.maxclique.graph cimport DSatur, Graph, NodeWrapper
from bnbpy.cython.problem cimport Problem


cdef class MaxClique(Problem):

    cdef readonly:
        list[NodeWrapper] C
        Graph G
        DSatur dsatur

    cdef inline void _set_graph(self, graph: Graph):
        self.G = graph
        self._init_dsatur()

    cdef inline void _append_to_clique(self, node: NodeWrapper):
        self.C.append(node)

    cdef inline void _init_dsatur(self):
        self.dsatur = DSatur(self.G)

    cpdef double calc_bound(self)

    cpdef bool is_feasible(self)

    cpdef list[Problem] branch(self)

    cpdef MaxClique copy(self, bool deep=*)

    cpdef MaxClique child_copy(self, bool deep=*)

    cpdef Problem warmstart(self)

    cdef void _inner_warmstart(self)
