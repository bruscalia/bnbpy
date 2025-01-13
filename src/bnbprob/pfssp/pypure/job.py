import copy
from dataclasses import dataclass
from typing import List

import numpy as np


@dataclass
class Job:
    """Job representation in permutation flow-shop scheduling problem"""

    j: int
    """Job index"""
    p: List[int]
    """Job processing time on each machine"""
    r: List[int]
    """
    Job release date on each machine based on partial solution
    (1 | :math:`r_j` , :math:`q_j` | :math:`sum_{j in J}{w_j C_j}`)
    """
    q: List[int]
    """
    Job delivery time on each machine based on partial solution
    (1 | :math:`r_j` , :math:`q_j` | :math:`sum_{j in J}{w_j C_j}`)
    """
    lat: np.ndarray[tuple[int, int], int]
    """Job latency between two machines `sum(p_i k < i < m)`"""

    def __repr__(self) -> str:
        return self._signature

    def __str__(self) -> str:
        return self._signature

    @property
    def _signature(self):
        return f'Job {self.j}'

    @property
    def slope(self):
        """Slope in fast initialization heuristic"""
        m = len(self.p) + 1
        s = 0
        for k in range(1, m):
            s += (k - (m + 1) / 2) * self.p[k - 1]
        return s

    @property
    def T(self):
        """Total processing time initialization heuristic"""
        return sum(self.p)

    @staticmethod
    def start_job(j: int, p: list[int]):
        return start_job(j, p)

    def copy(self, deep=False):
        if deep:
            return copy.deepcopy(self)
        other = Job(
            self.j,
            self.p,
            copy.copy(self.r),
            copy.copy(self.q),
            self.lat
        )
        return other


def start_job(j: int, p: list[int]) -> Job:
    m = len(p)

    r = [0] * m
    q = [0] * m

    # Resize `lat` to m x m
    lat = np.zeros((m, m), dtype='i')

    # Compute sums
    T = 0
    for m1 in range(m):
        T += p[m1]
        for m2 in range(m):
            if m2 + 1 < m1:  # Ensure range is valid
                sum_p = 0
                for i in range(m2 + 1, m1):
                    sum_p += p[i]
                lat[m1, m2] = sum_p

    job = Job(j, p, r, q, lat)

    return job
