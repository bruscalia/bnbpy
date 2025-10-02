import random

from pydantic.dataclasses import dataclass


@dataclass
class AssemblyFlowShopInstance:
    p: list[list[int]]
    """Processing times for each job (row) on each machine (column)"""
    edges: list[tuple[int, int]]
    """Directed edges representing machine precedences"""


def random_parallel_semilines(
    n_jobs: int, n_machines: tuple[int, int], seed: int | None = None
) -> AssemblyFlowShopInstance:
    """Generate a random instance of AssemblyFlowShop.

    Parameters
    ----------
    n_jobs : int
        The number of jobs.

    n_machines : tuple[int, int]
        The number of machines in each semiline.

    seed : int | None, optional
        The random seed, by default None.

    Returns
    -------
    AssemblyFlowShopInstance
        The generated AssemblyFlowShopInstance.
    """
    random.seed(seed)
    M = n_machines[0] + n_machines[1] - 1
    p = [[random.randint(1, 100) for _ in range(M)] for _ in range(n_jobs)]
    edges = parallel_semilines_edges(n_machines)
    return AssemblyFlowShopInstance(p, edges)


def parallel_semilines_edges(
    n_machines: tuple[int, int],
) -> list[tuple[int, int]]:
    """Generate directed edges for an AssemblyFlowShop with parallel semilines.

    Parameters
    ----------
    n_machines : tuple[int, int]
        The number of machines in each semiline.

    Returns
    -------
    list[tuple[int, int]]
        Directed edges representing machine precedences.
    """
    M = n_machines[0] + n_machines[1] - 1
    edges = []
    for i in range(n_machines[0] - 2):
        edges.append((i, i + 1))
    for i in range(n_machines[0] - 1, M - 1):
        edges.append((i, i + 1))
    edges.append((n_machines[0] - 2, M - 1))
    return edges


def random_dpm(
    n_jobs: int, n_machines: tuple[int, int], seed: int | None = None
) -> AssemblyFlowShopInstance:
    """Generate a random instance of DPM layout.

    Parameters
    ----------
    n_jobs : int
        The number of jobs.

    n_machines : tuple[int, int]
        The total number of machines and the number
        of machines in the assembly stage.

    seed : int | None, optional
        The random seed, by default None.

    Returns
    -------
    AssemblyFlowShopInstance
        The generated AssemblyFlowShopInstance.
    """
    random.seed(seed)
    M = n_machines[0] + n_machines[1]
    p = [[random.randint(1, 100) for _ in range(M)] for _ in range(n_jobs)]
    edges = dpm_layout_edges(n_machines[0], n_machines[1])
    return AssemblyFlowShopInstance(p, edges)


def dpm_layout_edges(
    first_stage: int, assembly_stage: int
) -> list[tuple[int, int]]:
    """Generate directed edges for a DPM layout.

    Parameters
    ----------
    first_stage : int
        The number of machines in the first stage.

    assembly_stage : int
        The number of machines in the assembly stage.

    Returns
    -------
    list[tuple[int, int]]
        Directed edges representing machine precedences.
    """
    edges = []
    total_machines = first_stage + assembly_stage
    for i in range(first_stage):
        edges.append((i, first_stage))
    for i in range(first_stage, total_machines - 1):
        edges.append((i, i + 1))
    return edges
