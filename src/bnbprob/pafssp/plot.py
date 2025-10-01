from typing import Any, List, Optional, Union

import gif
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Colormap, ListedColormap

from bnbprob.pafssp.cython.pyjob import PyJob as Job

MAX_LABEL = 10


class RandomCmap:
    def __init__(self, seed: int | None = None):
        self._rng = np.random.default_rng(seed)

    def create(self, size: int) -> ListedColormap:
        random_colors = self._rng.random(size=(size, 3))
        return ListedColormap(random_colors, name='random_colormap')


def plot_gantt(  # noqa: PLR0913, PLR0917
    jobs: List[Job],
    figsize: Optional[tuple[int, int]] = None,
    cmap: Optional[Union[list[Any], Colormap, str]] = None,
    dpi: int = 100,
    filename: Optional[str] = None,
    seed: int | None = None,
    label_cols: int = 1,
    label_fontsize: int = 8,
    max_label: int = MAX_LABEL,
) -> None:
    _ = _plot_gantt(
        jobs,
        figsize,
        cmap,
        dpi,
        filename,
        seed,
        label_cols,
        label_fontsize,
        max_label,
    )
    plt.show()


def draw_gantt_gif(  # noqa: PLR0913, PLR0917
    jobs: List[List[Job]],
    figsize: Optional[tuple[int, int]] = None,
    cmap: Optional[Union[list[Any], Colormap, str]] = None,
    dpi: int = 100,
    filename: Optional[str] = None,
    seed: int | None = None,
    duration: int = 200,
    label_cols: int = 1,
    label_fontsize: int = 8,
    max_label: int = MAX_LABEL,
) -> None:
    J = len(jobs[-1])

    # Define a color map for the jobs
    colors: Any
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
        raise ValueError('Bad argument for cmap')

    @gif.frame  # type: ignore
    def new_frame(i: int) -> None:
        c = [colors(job.j % J) for job in jobs[i]]
        _ = _plot_gantt(
            jobs[i],
            figsize=figsize,
            cmap=c,
            dpi=dpi,
            filename=None,
            seed=seed,
            label_cols=label_cols,
            label_fontsize=label_fontsize,
            max_label=max_label
        )

    # Construct "frames"
    frames = [new_frame(i) for i in range(len(jobs))]

    # Save "frames" to gif with a specified duration (milliseconds)
    # between each frame
    gif.save(frames, filename, duration=duration)
    plt.close()


def _plot_gantt(  # noqa: PLR0913, PLR0917
    jobs: List[Job],
    figsize: Optional[tuple[int, int]] = None,
    cmap: Optional[Union[list[Any], Colormap, str]] = None,
    dpi: int = 100,
    filename: Optional[str] = None,
    seed: int | None = None,
    label_cols: int = 1,
    label_fontsize: int = 8,
    max_label: int = MAX_LABEL,
) -> plt.Axes:  # type: ignore
    """
    Plots a Gantt chart for a given list of Job objects in a sequence.

    Parameters:
        jobs (List[Job]): A list of Job objects representing the sequence.
    """
    if figsize is None:
        figsize = (7, 3)

    _, ax = plt.subplots(figsize=figsize, dpi=dpi)

    # Get dimensions
    M = len(jobs[0].p)
    J = len(jobs)

    # Define a color map for the jobs
    colors: Any
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
        raise ValueError('Bad argument for cmap')

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

    if len(jobs) <= max_label:
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(
            by_label.values(),
            by_label.keys(),
            loc='upper left',
            bbox_to_anchor=(1.0, 1.0),
            ncol=label_cols,
            fontsize=label_fontsize,
        )

    plt.tight_layout()

    if filename:
        plt.savefig(filename)

    return ax
