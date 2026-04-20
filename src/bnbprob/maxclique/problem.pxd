# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector

from bnbprob.maxclique.graph cimport (
    DSatur,
    Graph,
    NodeWrapper,
    wrap_node
)
from bnbprob.maxclique.node cimport Node, c_find_max_node_degree
from bnbpy.cython.problem cimport Problem
from bnbpy.cython.solution cimport Solution


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

    cpdef list[MaxClique] branch(self)

    cpdef MaxClique child_copy(self, bool deep=*)

    cdef void _inner_warmstart(self)
