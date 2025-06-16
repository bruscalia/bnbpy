from typing import Any, Dict, List, Optional, Tuple

import gif
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib import colormaps
from matplotlib.colors import ListedColormap

from bnbprob.gcol.coloring import ColorNode
from bnbprob.gcol.indset import IndepSetNode
from bnbprob.milpy import MILPSol

INT_TOL = 0.5
SMALL = 1e-6


def draw_gc_from_nodes(nodes: Dict[int, ColorNode], **kwargs: Any) -> None:
    N = [n.index for n in nodes.values()]
    N.sort(reverse=False)
    C = [nodes[n].color.index for n in N if nodes[n].color is not None]  # type: ignore
    E = [(n.index, m.index) for n in nodes.values() for m in n.neighbors]
    E.sort(reverse=False)
    _draw_colored_graph(N, C, E, **kwargs)
    # Show the plot if no axis provided (for standalone usage)
    if kwargs.get('ax', None) is None:
        plt.show()


def draw_colored_gif(  # noqa: PLR0913, PLR0917
    filename: str,
    nodes: Dict[int, ColorNode],
    history: List[ColorNode],
    uncolored_color: Optional[Any] = 'grey',
    node_size: int = 200,
    node_alpha: float = 1.0,
    edge_color: Any = 'grey',
    edge_alpha: float = 0.2,
    duration: int = 200,
    **kwargs: Any,
) -> None:
    N = [n.index for n in nodes.values()]
    C = {n.index: n.color.index for n in nodes.values() if n.color is not None}
    E = [(n.index, m.index) for n in nodes.values() for m in n.neighbors]
    N.sort(reverse=False)
    E.sort(reverse=False)

    @gif.frame  # type: ignore
    def new_frame(i: int) -> None:
        Ni = [n for n in N if nodes[n] in history[:i]]
        Nx = [n for n in N if nodes[n] in history[i:]]
        Ci = [C[i] for i in Ni]
        node = history[i - 1]
        Ei = [(node.index, j.index) for j in node.neighbors]
        G, pos, ax = _draw_colored_graph(
            Ni,
            Ci,
            E,
            node_alpha=node_alpha,
            node_size=node_size,
            edge_color=edge_color,
            edge_alpha=edge_alpha,
            **kwargs,
        )
        nx.draw_networkx_nodes(
            G,
            pos,
            nodelist=Nx,
            node_color=uncolored_color,
            node_size=node_size,
            ax=ax,
            alpha=0.5 * node_alpha,
        )
        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=Ei,
            ax=ax,
            alpha=edge_alpha * 0.5,
            edge_color=edge_color,
        )

    # Construct "frames"
    frames = [new_frame(i + 1) for i in range(len(history))]

    # Save "frames" to gif with a specified duration (milliseconds)
    # between each frame
    gif.save(frames, filename, duration=duration)
    plt.close()


def draw_mis_from_nodes(
    nodes: Dict[int, IndepSetNode],
    active_color: Any = 'firebrick',
    inactive_color: Any = 'grey',
    **kwargs: Any,
) -> None:
    N = [n.index for n in nodes.values()]
    C = [int(n.selected) for n in nodes.values()]
    E = [(n.index, m.index) for n in nodes.values() for m in n.neighbors]
    _draw_colored_graph(
        N, C, E, plot_colors=[inactive_color, active_color], **kwargs
    )
    # Show the plot if no axis provided (for standalone usage)
    if kwargs.get('ax', None) is None:
        plt.show()


def draw_mis_gif(  # noqa: PLR0913, PLR0917
    filename: str,
    nodes: Dict[int, IndepSetNode],
    history: List[IndepSetNode],
    active_color: Any = 'firebrick',
    inactive_color: Any = 'grey',
    node_size: int = 200,
    node_alpha: float = 1.0,
    edge_color: Any = 'grey',
    edge_alpha: float = 0.2,
    duration: int = 200,
    **kwargs: Any,
) -> None:
    N = [n.index for n in nodes.values()]
    C = {n.index: int(n.selected) for n in nodes.values()}
    E = [(n.index, m.index) for n in nodes.values() for m in n.neighbors]

    @gif.frame  # type: ignore
    def new_frame(i: int) -> None:
        Ni = [n for n in N if nodes[n] in history[:i]]
        Nx = [n for n in N if nodes[n] not in history[:i]]
        Ci = [C[i] for i in Ni]
        node = history[i - 1]
        Ei = [(node.index, j.index) for j in node.neighbors]
        G, pos, ax = _draw_colored_graph(
            Ni,
            Ci,
            E,
            plot_colors=[inactive_color, active_color],
            node_alpha=node_alpha,
            node_size=node_size,
            edge_color=edge_color,
            edge_alpha=edge_alpha,
            **kwargs,
        )
        nx.draw_networkx_nodes(
            G,
            pos,
            nodelist=Nx,
            node_color=inactive_color,
            node_size=node_size,
            ax=ax,
            alpha=0.5 * node_alpha,
        )
        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=Ei,
            ax=ax,
            alpha=edge_alpha * 0.5,
            edge_color=edge_color,
        )

    # Construct "frames"
    frames = [new_frame(i + 1) for i in range(len(history))]

    # Save "frames" to gif with a specified duration (milliseconds)
    # between each frame
    gif.save(frames, filename, duration=duration)
    plt.close()


def _draw_colored_graph(  # noqa: PLR0913, PLR0917
    nodes: List[int],
    colors: List[int],
    edges: List[Tuple[int, int]],
    ax: Optional[plt.Axes] = None,  # type: ignore
    plot_colors: Optional[List[Tuple[float, float, float]]] = None,
    node_size: int = 200,
    node_alpha: float = 1.0,
    font_size: int = 8,
    edge_color: Any = 'grey',
    edge_alpha: float = 0.2,
    use_labels: bool = True,
    plot_margins: bool = True,
    layout_iter: int = 100,
    seed: Optional[int] = None,
) -> Tuple[nx.Graph, Dict[int, Tuple[float, float]], plt.Axes]:  # type: ignore
    # Create a list of colors base on two colormaps
    if plot_colors is None:
        plot_colors = (
            colormaps['Dark2'].colors  # type: ignore
            + colormaps['Set1'].colors  # type: ignore
            + colormaps['Set2'].colors  # type: ignore
            + colormaps['Set3'].colors  # type: ignore
        )

    # Expand plot_colors to handle any number of distinct colors
    if len(colors) >= 1:
        while len(plot_colors) < max(colors) + 1:
            plot_colors += plot_colors  # Duplicate colors list

    # Create a networkx graph from the edges
    G = nx.Graph()
    G.add_edges_from(edges)

    # Map the nodes to the colors from the color_map
    node_color_list = [plot_colors[color] for color in colors]

    # Draw the graph
    pos = nx.spring_layout(
        G, iterations=layout_iter, seed=seed
    )  # positions for all nodes, you can use other layouts like shell,
    # random, etc.
    nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=nodes,
        node_color=node_color_list,
        node_size=node_size,
        ax=ax,
        alpha=node_alpha,
    )
    nx.draw_networkx_edges(
        G, pos, ax=ax, alpha=edge_alpha, edge_color=edge_color
    )
    if use_labels:
        nx.draw_networkx_labels(G, pos, ax=ax, font_size=font_size)

    # Possibly remove margins
    if not plot_margins:
        plt.axis('off')
        plt.tight_layout()

    return G, pos, ax


def plot_columns_gcol(
    sol: MILPSol,
    figsize: Optional[tuple[int, int]] = None,
    dpi: int = 100,
    plot_colors: Optional[list[Any]] = None,
) -> None:
    if figsize is None:
        figsize = (7, 3)

    # Create a mask for all columns
    if sol.problem.A_ub is None:
        raise ValueError(
            'The problem does not have an upper bound matrix A_ub.'
        )
    if sol.x is None:
        raise ValueError('The solution does not have a variable vector x.')
    columns = (-sol.problem.A_ub > INT_TOL).astype(int)
    cols_x = np.nonzero(sol.x > INT_TOL)[0]

    # Create a list of colors base on two colormaps
    if plot_colors is None:
        plot_colors = (
            colormaps['Dark2'].colors  # type: ignore
            + colormaps['Set1'].colors  # type: ignore
            + colormaps['Set2'].colors  # type: ignore
            + colormaps['Set3'].colors  # type: ignore
        )

    cmap = ListedColormap(
        [(1, 1, 1, 0), (0, 0, 0, 0.2), *plot_colors], N=len(plot_colors) + 2
    )

    # Plot all columns in gray
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    for k, i in enumerate(cols_x):
        # Create a mask for the current selected column
        columns[:, i] = (k + 2) * columns[:, i]

    columns[-sol.problem.A_ub < SMALL] = 0
    _ = ax.matshow(columns - 0.5, cmap=cmap, vmin=0.1)

    # Turn off axis
    plt.axis('off')
    fig.tight_layout()
    plt.show()
