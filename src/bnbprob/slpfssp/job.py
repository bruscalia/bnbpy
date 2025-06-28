import copy

import numpy as np
from numpy.typing import NDArray


class Job:
    """Job representation in permutation flow-shop scheduling problem"""

    j: int
    """Job index"""
    p: list[list[int]]
    """Job processing time on each machine of each parallel semiline"""
    r: list[list[int]]
    """
    Job release date on each machine of each parallel semiline
    based on partial solution
    (1 | :math:`r_j` , :math:`q_j` | :math:`sum_{j in J}{w_j C_j}`)
    """
    q: list[list[int]]
    """
    Job delivery time on each machine of each parallel semiline
    based on partial solution
    (1 | :math:`r_j` , :math:`q_j` | :math:`sum_{j in J}{w_j C_j}`)
    """
    lat: list[NDArray[np.int_]]
    """Job latency between two machines of each semiline
    `sum(p_i k < i < m)`"""
    m: list[int]
    """Number of machines on each parallel semiline"""
    L: int
    """Number of parallel semilines"""
    s: int
    """Number of reconciliation machines"""

    def __init__(self, j: int, p: list[list[int]], s: int = 1) -> None:
        self.j = j
        self.p = p
        self.s = s

        L = len(p)
        m = [len(p_i) for p_i in p]
        r = [[0] * m_i for m_i in m]
        q = [[0] * m_i for m_i in m]
        lat = [_fill_lat(p_i) for p_i in p]

        self.r = r
        self.q = q
        self.lat = lat

        self.m = m
        self.L = L

    def __repr__(self) -> str:
        return self._signature

    def __str__(self) -> str:
        return self._signature

    @property
    def _signature(self) -> str:
        return f'Job {self.j}'

    @property
    def T(self) -> int:
        """Total processing time initialization heuristic"""
        return sum(sum(p_i) for p_i in self.p)

    @staticmethod
    def from_job(job: 'Job') -> 'Job':
        return job.copy(deep=False)

    def copy(self, deep: bool = False) -> 'Job':
        if deep:
            return copy.deepcopy(self)
        other = Job.__new__(Job)
        other.j = self.j
        other.p = self.p
        other.r = [r_i.copy() for r_i in self.r]
        other.q = [q_i.copy() for q_i in self.q]
        other.lat = self.lat
        other.m = self.m
        other.L = self.L
        other.s = self.s
        return other


def start_job(j: int, p: list[list[int]], s: int = 1) -> Job:
    return Job(j, p, s)


def _fill_lat(p: list[int]) -> NDArray[np.int_]:
    m = len(p)

    # Resize `lat` to m x m
    lat = np.zeros((m, m), dtype='i')

    # Compute sums
    for m1 in range(m):
        for m2 in range(m):
            if m2 + 1 < m1:  # Ensure range is valid
                sum_p = 0
                for i in range(m2 + 1, m1):
                    sum_p += p[i]
                lat[m1, m2] = sum_p

    return lat
