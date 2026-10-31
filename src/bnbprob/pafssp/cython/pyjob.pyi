from typing import Optional

class PyJob:
    """Python wrapper holding a copy of a C++ ``Job``.

    Start times ``s`` are not part of the C++ job: they are only filled
    for jobs exported by ``PermFlowShop.sequence`` and are empty
    otherwise.
    """

    j: int
    """Job index"""
    p: list[int]
    """Processing times on each machine"""
    r: list[int]
    """Release dates on each machine"""
    q: list[int]
    """Wait times (tails) on each machine"""
    lat: list[list[int]]
    """Latencies between pairs of machines"""
    slope: int
    """Slope index (Palmer, 1965)"""
    T: int
    """Total processing time"""
    s: list[int]
    """Start times on each machine (empty unless exported by
    ``PermFlowShop.sequence``)."""

    @staticmethod
    def from_p(
        j: int, p: list[int], edges: Optional[list[tuple[int, int]]] = None
    ) -> 'PyJob':
        """Create a standalone job from its processing times.

        Parameters
        ----------
        j : int
            Job index

        p : list[int]
            Processing times on each machine

        edges : Optional[list[tuple[int, int]]], optional
            Machine graph edges, by default None (sequential)

        Returns
        -------
        PyJob
            New job owning its data
        """
        ...
