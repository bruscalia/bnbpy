from typing import Any

import matplotlib.pyplot as plt

from bnbprob.gcol.plot import _draw_colored_graph  # noqa: PLC2701
from bnbprob.maxclique.graph import Graph
from bnbprob.maxclique.problem import MaxClique


def plot_clique(
    graph: Graph,
    solution: MaxClique,
    clique_color: str = 'firebrick',
    other_color: str = 'grey',
    **kwargs: Any,
) -> None:
    nodes_list = graph.nodes
    clique_indices = {node.index for node in solution.clique}
    N = [n.index for n in nodes_list]
    C = [int(n.index in clique_indices) for n in nodes_list]
    E = [(n.index, m) for n in nodes_list for m in n.neighbors]
    _draw_colored_graph(
        N,
        C,
        E,
        plot_colors=[other_color, clique_color],
        **kwargs,
    )
    plt.show()
