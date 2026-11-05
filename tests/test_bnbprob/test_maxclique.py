import itertools
from typing import Any, Callable

import networkx as nx
import pytest

from bnbprob.maxclique import Graph, MaxClique, random_graph
from bnbpy import BestFirstBnB, BranchAndBound, BreadthFirstBnB, LifoBnB

SOLVERS: dict[str, Callable[..., BranchAndBound[MaxClique]]] = {
    'lifo': LifoBnB,
    'dfs': BranchAndBound,
    'bfs': BreadthFirstBnB,
    'best': BestFirstBnB,
}


def nx_clique_size(edges: list[tuple[int, int]]) -> int:
    graph: Any = nx.Graph(edges)
    _, size = nx.max_weight_clique(graph, weight=None)
    return int(size)


def assert_clique(edges: list[tuple[int, int]], clique: list[int]) -> None:
    edge_set = {frozenset(e) for e in edges}
    for i, j in itertools.combinations(clique, 2):
        assert frozenset((i, j)) in edge_set


@pytest.mark.integration
class TestMaxClique:
    @staticmethod
    @pytest.mark.parametrize('eval_node', ['in', 'out', 'both'])
    @pytest.mark.parametrize('solver', list(SOLVERS))
    def test_complete_graph(solver: str, eval_node: str) -> None:
        edges = list(itertools.combinations(range(5), 2))
        res = SOLVERS[solver](
            MaxClique(Graph.from_edges(edges)), eval_node=eval_node
        ).solve()
        assert res.cost == -5  # noqa: PLR2004

    @staticmethod
    def test_cycle() -> None:
        edges = [(i, (i + 1) % 5) for i in range(5)]
        res = LifoBnB(MaxClique(Graph.from_edges(edges))).solve()
        assert res.cost == -2  # noqa: PLR2004

    @staticmethod
    @pytest.mark.parametrize('eval_node', ['in', 'out', 'both'])
    @pytest.mark.parametrize('solver', list(SOLVERS))
    @pytest.mark.parametrize('seed', range(6))
    def test_random_graphs(solver: str, eval_node: str, seed: int) -> None:
        edges = random_graph(20, 0.5, seed=seed)
        res = SOLVERS[solver](
            MaxClique(Graph.from_edges(edges)), eval_node=eval_node
        ).solve()
        clique = [node.index for node in res.problem.clique]
        assert -res.cost == len(clique)
        assert len(clique) == nx_clique_size(edges)
        assert_clique(edges, clique)

    @staticmethod
    def test_warmstart_is_a_clique() -> None:
        edges = random_graph(30, 0.4, seed=1)
        sol = MaxClique(Graph.from_edges(edges)).warmstart()
        clique = [node.index for node in sol.clique]
        assert clique
        assert_clique(edges, clique)

    @staticmethod
    def test_graph_from_edges() -> None:
        graph = Graph.from_edges([(0, 1), (1, 2)])
        assert graph.num_nodes == 3  # noqa: PLR2004
        neighbors = {
            node.index: sorted(node.neighbors) for node in graph.nodes
        }
        assert neighbors == {0: [1], 1: [0, 2], 2: [1]}
        assert graph.are_neighbors(0, 1)
        assert not graph.are_neighbors(0, 2)

    @staticmethod
    def test_empty_graph() -> None:
        res = BranchAndBound(MaxClique(Graph.from_edges([]))).solve()
        assert res.cost == 0

    @staticmethod
    def test_copy() -> None:
        problem = MaxClique(Graph.from_edges([(0, 1)]))
        problem.compute_bound()
        deep = problem.copy()
        shallow = problem.copy(deep=False)
        assert deep.solution is not problem.solution
        assert deep.solution.lb == problem.solution.lb
        assert shallow.solution is problem.solution
        assert deep.graph is problem.graph

    @staticmethod
    def test_random_graph_is_reproducible() -> None:
        assert random_graph(15, 0.3, seed=4) == random_graph(15, 0.3, seed=4)
