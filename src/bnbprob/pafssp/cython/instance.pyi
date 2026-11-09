from typing import Any, Optional

from bnbprob.pafssp.instances import AssemblyFlowShopInstance
from bnbprob.pafssp.machinegraph import MachineGraph

class FlowShopInstanceData:
    """Immutable data of a (assembly) permutation flow-shop instance.

    Owns the C++ jobs, the machine graph, and the two-machine (LB5)
    cache shared by every :class:`PermFlowShop` node built from it.
    Each node keeps a reference to this object in its ``data``
    attribute, so the instance lives as long as any node does.

    Build it with :meth:`from_p` or :meth:`from_instance`; calling the
    class directly gives an uninitialized object.
    """

    @property
    def p(self) -> list[list[int]]:
        """Copy of the processing times for each job (row) on each
        machine (column). Treat as read-only."""
        ...

    @property
    def edges(self) -> list[tuple[int, int]]:
        """Copy of the machine-precedence edges. Treat as read-only."""
        ...

    @classmethod
    def from_p(
        cls,
        p: list[list[int]],
        edges: Optional[list[tuple[int, int]]] = None,
    ) -> 'FlowShopInstanceData':
        """Instantiate from processing times and machine-graph edges.

        Parameters
        ----------
        p : list[list[int]]
            Processing times for each job (row) on each machine (column)

        edges : Optional[list[tuple[int, int]]], optional
            Machine-precedence edges, by default None (sequential)

        Returns
        -------
        FlowShopInstanceData
            Instance data

        Raises
        ------
        ValueError
            If ``p`` is empty, has rows of different lengths, or its
            number of columns differs from the number of machines in the
            graph. ``CyclicGraphError`` (a ``ValueError``) if the edges
            contain a cycle.
        """
        ...

    @classmethod
    def from_instance(
        cls, instance: AssemblyFlowShopInstance
    ) -> 'FlowShopInstanceData':
        """Instantiate from an ``AssemblyFlowShopInstance``.

        Parameters
        ----------
        instance : AssemblyFlowShopInstance
            Instance with processing times ``p`` and machine-precedence
            ``edges``

        Returns
        -------
        FlowShopInstanceData
            Instance data
        """
        ...

    def to_instance(self) -> AssemblyFlowShopInstance:
        """Export as an ``AssemblyFlowShopInstance``.

        Returns
        -------
        AssemblyFlowShopInstance
            Instance with copies of ``p`` and ``edges``
        """
        ...

    @property
    def n(self) -> int:
        """Number of jobs"""
        ...

    @property
    def m(self) -> int:
        """Number of machines"""
        ...

    @property
    def mach_graph(self) -> MachineGraph:
        """Machine graph (Python copy of the C++ graph)"""
        ...

    def __reduce__(self) -> tuple[Any, ...]: ...
