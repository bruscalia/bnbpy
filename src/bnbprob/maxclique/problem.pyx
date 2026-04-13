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

    def __init__(self, graph: Graph):
        super().__init__()
        self.C = []
        self.G = graph
        self.dsatur = DSatur(self.G)

    @property
    def clique(self) -> list[NodeWrapper]:
        return self.C

    @property
    def graph(self) -> Graph:
        return self.G

    cpdef double calc_bound(self):
        self.dsatur.solve()
        return - len(self.C) - self.dsatur.bound

    cpdef bool is_feasible(self):
        return self.G.num_nodes == 0

    cpdef list[MaxClique] branch(self):
        cdef:
            Node* selected_node
            Graph child_graph1, child_graph2
            MaxClique child_problem1, child_problem2

        if self.G.num_nodes == 0:
            return []

        # Select node by DSatur criteria
        selected_node = self.G.c_next_node()

        # First child includes the selected node in the clique
        child_graph1 = self.G.copy_branch(selected_node.index)
        child_problem1 = self.child_copy(deep=False)
        child_problem1._set_graph(child_graph1)
        child_problem1._append_to_clique(wrap_node(selected_node))

        # Second child excludes the selected node from the clique
        child_graph2 = self.G.copy_remove(selected_node.index)
        child_problem2 = self.child_copy(deep=False)
        child_problem2._set_graph(child_graph2)

        return [child_problem2, child_problem1]

    cpdef MaxClique child_copy(self, bool deep=True):
        cdef:
            MaxClique new_problem

        new_problem = MaxClique.__new__(MaxClique)
        new_problem.solution = Solution()
        new_problem.C = self.C.copy()
        new_problem.G = self.G
        new_problem.dsatur = self.dsatur
        return new_problem

    cpdef MaxClique warmstart(self):
        cdef:
            MaxClique child_problem

        child_problem = self.child_copy(deep=False)
        child_problem._inner_warmstart()
        return child_problem

    cdef void _inner_warmstart(self):
        cdef:
            Graph new_graph
            Node* node
            vector[Node*] nodes
            int i

        new_graph = self.G
        for i in range(new_graph.get_active_size()):
            nodes = new_graph.get_nodes()
            node = c_find_max_node_degree(nodes)
            self.C.append(wrap_node(node))
            new_graph = new_graph.copy_branch(node.index)
            if new_graph.get_active_size() == 0:
                break
        self._set_graph(new_graph)
