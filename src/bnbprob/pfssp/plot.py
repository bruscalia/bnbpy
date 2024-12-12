from typing import List, Optional, Union

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Colormap, ListedColormap

from bnbprob.pfssp.job import Job

MAX_LABEL = 10


class RandomCmap:

    def __init__(self, seed=None):
        self._rng = np.random.default_rng(seed)

    def create(self, size):
        random_colors = self._rng.random(size=(size, 3))
        return ListedColormap(random_colors, name='random_colormap')


def plot_gantt(  # noqa: PLR0913, PLR0917
    jobs: List[Job],
    figsize=None,
    cmap: Optional[Union[list, Colormap, str]] = None,
    dpi=100,
    filename: Optional[str] = None,
    seed=None,
):
    """
    Plots a Gantt chart for a given list of Job objects in a sequence.

    Parameters:
        jobs (List[Job]): A list of Job objects representing the sequence.
    """
    if figsize is None:
        figsize = [7, 3]

    _, ax = plt.subplots(figsize=figsize, dpi=dpi)

    # Get dimensions
    M = len(jobs[0].p)
    J = len(jobs)

    # Define a color map for the jobs
    if cmap is None:
        rcmap = RandomCmap(seed)
        colors = rcmap.create(J)
    elif isinstance(cmap, list):
        colors = ListedColormap(cmap)
    elif isinstance(cmap, str):
        colors = plt.get_cmap(cmap, len(jobs))
    elif isinstance(cmap, Colormap):
        colors = cmap
    else:
        raise ValueError("Bad argument for cmap")

    # Iterate over the jobs to plot them on the Gantt chart
    for j, job in enumerate(jobs):
        color = colors(j % J)  # Get a unique color for each job
        for m in range(M):
            start_time = job.r[m] if job.r and job.r[m] is not None else 0
            end_time = start_time + job.p[m]

            # Plot a bar for each job on each machine with consistent color
            ax.barh(
                y=f'M {m + 1}',
                width=end_time - start_time,
                left=start_time,
                height=0.4,
                color=color,
                label=f'Job {job.j}' if m == 0 else None,
                align='center',
            )

    # Labeling and legend
    ax.set_xlabel('Time')

    if len(jobs) <= MAX_LABEL:
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(
            by_label.values(),
            by_label.keys(),
            loc='upper left',
            bbox_to_anchor=(1.0, 1.0),
        )

    plt.tight_layout()

    if filename:
        plt.savefig(filename)

    plt.show()
