import copy
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Job:
    """Job representation in permutation flow-shop scheduling problem"""

    j: int
    """Job index"""
    p: List[int]
    """Job processing time on each machine"""
    r: Optional[List[int]] = None
    """
    Job release date on each machine based on partial solution
    (1 | :math:`r_j` , :math:`q_j` | :math:`sum_{j in J}{w_j C_j}`)
    """
    q: Optional[List[int]] = None
    """
    Job delivery time on each machine based on partial solution
    (1 | :math:`r_j` , :math:`q_j` | :math:`sum_{j in J}{w_j C_j}`)
    """
    lat: Optional[List[List[int]]] = None
    """Job latency between two machines `sum(p_i k < i < m)`"""

    @property
    def _signature(self):
        return f'Job {self.j}'

    def fill_start(self, m: int):
        self.r = [0 for _ in range(m)]
        self.q = [0 for _ in range(m)]
        self.lat = [
            [sum(self.p[i] for i in range(m2 + 1, m1)) for m2 in range(m)]
            for m1 in range(m)
        ]
        m += 1
        self.slope = sum(
            (k - (m + 1) / 2) * self.p[k - 1] for k in range(1, m)
        )

    def copy(self, deep=False):
        if deep:
            return copy.deepcopy(self)
        other = Job(
            self.j,
            self.p,
            copy.copy(self.r),
            copy.copy(self.q),
            self.lat,
        )
        other.slope = self.slope
        return other

    def __repr__(self) -> str:
        return self._signature

    def __str__(self) -> str:
        return self._signature
