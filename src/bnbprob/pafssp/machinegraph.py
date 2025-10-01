import networkx as nx
from pydantic.dataclasses import dataclass


class CyclicGraphError(ValueError):
    """Exception raised when a cyclic
    graph is detected where a DAG is expected."""

    pass


@dataclass
class MachineGraph:
    M: int
    prec: list[list[int]]
    succ: list[list[int]]
    topo_order: list[int]
    rev_topo_order: list[int]
    descendants: list[list[int]]

    @classmethod
    def from_edges(self, edges: list[tuple[int, int]]) -> 'MachineGraph':
        """Creates a MachineGraph from a list of directed edges.

        Parameters
        ----------
        edges : list[tuple[int, int]]
            Edges of a directed acyclic graph (DAG)
            representing machine precedences.

        Returns
        -------
        MachineGraph
            A MachineGraph instance representing the given edges.

        Raises
        ------
        ValueError
            If the edge list is empty or contains a cycle.

        ValueError
            If the graph is not a DAG.
        """
        # Create directed graph from edges
        G = nx.DiGraph()
        G.add_edges_from(edges)

        # Check for cycles
        if not nx.is_directed_acyclic_graph(G):
            raise CyclicGraphError('The provided edges contain a cycle.')

        # Get number of machines
        N = list[int](G.nodes)
        M = max(N, default=-1) + 1

        # Get precedence and successor lists
        prec: list[list[int]] = [[] for _ in range(M)]
        succ: list[list[int]] = [[] for _ in range(M)]
        for i, j in edges:
            prec[j].append(i)
            succ[i].append(j)

        # Get topological order
        topo_order = list[int](nx.topological_sort(G))

        # Get reverse topological order
        rev_topo_order = topo_order.copy()
        rev_topo_order.reverse()

        # Identify descendants of machines (maximal paths)
        descendants = list[list[int]]([] for _ in range(M))
        for i in N:
            desc_nodes = list(nx.descendants(G, i))
            descendants[i] = desc_nodes

        return MachineGraph(
            M, prec, succ, topo_order, rev_topo_order, descendants
        )
