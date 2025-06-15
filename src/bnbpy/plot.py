from typing import Any, List, Optional, Union

import matplotlib.pyplot as plt
import networkx as nx

from bnbpy.node import Node
from bnbpy.status import OptStatus


def get_color(node: Node) -> str:  # noqa: PLR0911
    if node.parent is None:
        return 'cyan'
    if node.solution.status is OptStatus.OPTIMAL:
        return 'lightgreen'
    elif node.solution.status is OptStatus.FEASIBLE:
        return 'lightblue'
    elif node.lb == float('inf'):
        return 'lightcoral'
    elif node.solution.status is OptStatus.FATHOM:
        return 'darkgrey'
    elif node.children:
        return 'gold'
    return 'lightgrey'


class Edges(list[Any]):
    nodes: List[Node]

    def __init__(self, root: Node):
        super().__init__()
        self.nodes = []
        self.traverse(root)

    def traverse(self, node: Node) -> None:
        self.nodes.append(node)
        for child in node.children:
            self.append((node.index, child.index))
            self.traverse(child)

    @property
    def colors(self) -> dict[int, str]:
        return {node.index: get_color(node) for node in self.nodes}


def _format_lb(x: float | str) -> str:
    if isinstance(x, float):
        return f'{x:.1f}'
    else:
        return f'{x}'


def plot_tree(  # noqa: PLR0913, PLR0917
    root: Node,
    align: str = 'horizontal',
    show_lb: bool = True,
    custom_labels: Any = None,
    figsize: Optional[Union[tuple[Any, ...], list[Any]]] = None,
    dpi: int = 100,
    **options: Any
) -> None:
    """From the root node of a solved Branch & Bound, create a tree-plot

    Parameters
    ----------
    root : Node
        Root node of search tree

    align : str, optional
        Mode of alignment in `networkx.bfs_layout`, by default 'horizontal'

    show_lb : bool, optional
        Either or not to show lower bounds (custom_labels must be `None`),
        by default True

    custom_labels : Any, optional
        Custom labels parsed to `networkx.draw`, by default None

    figsize : Optional[Union[tuple, list]], optional
        Figure size parsed to `matplotlib`, by default None

    dpi : int, optional
        Dpi parsed to `matplotlib`, by default 100
    """
    if figsize is None:
        figsize = (8, 6)
    # Extract edges from the root node
    tree_edges = Edges(root)

    # Create a directed graph
    G: nx.DiGraph = nx.DiGraph()
    G.add_edges_from(tree_edges)

    # Draw the graph with a spring layout
    pos = nx.bfs_layout(
        G, start=root.index, align=align
    )  # You can use other layouts like shell_layout or circular_layout

    pos = {node: (x, -y) for node, (x, y) in pos.items()}
    color_code = tree_edges.colors
    colors = [color_code.get(node, 'lightgrey') for node in G.nodes()]
    if show_lb:
        custom_labels = {
            node.index: _format_lb(node.lb)
            + f'$_{ ({node.index}) }$'
            for node in tree_edges.nodes
        }

    plt.figure(figsize=figsize, dpi=dpi)
    nx.draw(
        G,
        pos,
        with_labels=True,
        labels=custom_labels,
        node_size=700,
        node_color=colors,
        arrows=False,
        **options
    )
    plt.show()
