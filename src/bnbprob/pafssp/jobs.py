"""Plain-Python views of the jobs and partial sequences of a
:class:`~bnbprob.pafssp.PermFlowShop` problem.

Instances are snapshots: their values are copied from the C++ data when
exported (e.g. by ``PermFlowShop.sequence``), so they stay valid after the
problem and its instance data are garbage-collected.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PyJob:
    """Snapshot of a job of a (assembly) permutation flow-shop problem.

    Start times ``s`` are only filled for jobs exported by
    ``PermFlowShop.sequence``; they are empty otherwise.
    """

    j: int
    """Job index"""
    p: list[int]
    """Processing times on each machine"""
    r: list[int]
    """Release dates (heads) on each machine"""
    q: list[int]
    """Wait times (tails) on each machine"""
    lat: list[list[int]]
    """Latencies between pairs of machines"""
    s: list[int] = field(default_factory=list)
    """Start times on each machine (empty unless exported by
    ``PermFlowShop.sequence``)"""

    def __repr__(self) -> str:
        return f'Job {self.j}'

    @property
    def T(self) -> int:
        """Total processing time"""
        return sum(self.p)

    @property
    def slope(self) -> int:
        """Slope index (Palmer, 1965)"""
        m = len(self.p) + 1
        return sum((k - (m + 1) // 2) * self.p[k - 1] for k in range(1, m))


@dataclass(frozen=True, slots=True)
class PySigma:
    """Snapshot of a partial sequence of jobs (``sigma1`` or ``sigma2``
    of a ``PermFlowShop`` node), without start times."""

    m: int
    """Number of machines"""
    jobs: list[PyJob]
    """Jobs in sequence order"""
    C: list[int]
    """Completion times of the partial sequence on each machine"""

    def __repr__(self) -> str:
        return f'Sigma(m={self.m}, jobs={len(self.jobs)})'
