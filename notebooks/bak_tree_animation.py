from typing import Any, Optional, Union

import gif
import matplotlib.pyplot as plt
import networkx as nx

from bnbpy.node import Node
from bnbpy.plot import Edges, _format_lb  # noqa: PLC2701
from bnbpy.search import BranchAndBound


class AltBnB(BranchAndBound):
    counter = 0

    def enqueue(self, node: Node):
        node.tree_counter = self.counter
        type(self).counter += 1


def animate_tree(  # noqa: PLR0913, PLR0917
    root: Node,
    align: str = 'horizontal',
    show_lb: bool = True,
    custom_labels: Any = None,
    figsize: Optional[Union[tuple, list]] = None,
    dpi: int = 100,
    **options
):
    if figsize is None:
        figsize = (8, 6)
    # Extract edges from the root node
    tree_edges = Edges(root)
    nodes = tree_edges.nodes

    # Create a directed graph
    G = nx.DiGraph()
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

    @gif.frame
    def new_frame(i: int):
        Nall = [n.index for n in nodes]
        Nx = [n.index for n in nodes if n.tree_counter <= i]
        Cx = [colors[j] for j, n in enumerate(nodes) if n.tree_counter <= i]
        Ex = [(j, k) for j, k in tree_edges if k in Nx]
        Lx = {j: lab for j, lab in custom_labels.items() if j in Nx}
        plt.figure(figsize=figsize, dpi=dpi)
        nx.draw(
            G,
            pos,
            nodelist=Nall,
            edgelist=[],
            with_labels=False,
            node_size=700,
            node_color=["whitesmoke" for _ in range(len(Nall))],
            arrows=False,
            **options
        )
        nx.draw(
            G,
            pos,
            nodelist=Nx,
            edgelist=Ex,
            with_labels=True,
            labels=Lx,
            node_size=700,
            node_color=Cx,
            arrows=False,
            **options
        )

    # Construct "frames"
    frames = [new_frame(i) for i in range(len(nodes))]

    # Save "frames" to gif with a specified duration (milliseconds)
    # between each frame
    gif.save(frames, "pfssp-bnb.gif", duration=200)
    plt.close()


# animate_tree(bnb_sm.root, figsize=[8, 8], font_size=10)
