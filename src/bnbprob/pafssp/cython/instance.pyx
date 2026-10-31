# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

from libcpp.vector cimport vector

from cython.operator cimport dereference as deref

from bnbprob.pafssp.cpp.environ cimport InstanceData, MachineGraph
from bnbprob.pafssp.cython.utils cimport create_machine_graph, get_mach_graph
from bnbprob.pafssp.machinegraph import MachineGraph as MachGraphInterface

INIT_ERROR = 'C++ InstanceData not initialized'


def _rebuild(cls, p, edges):
    """Unpickling helper: rebuild from processing times and edges."""
    return cls.from_p(p, edges)


cdef class FlowShopInstanceData:
    """Immutable data of a (assembly) permutation flow-shop instance.

    Owns the C++ jobs, the machine graph, and the two-machine (LB5)
    cache shared by every :class:`PermFlowShop` node built from it.
    Each node keeps a reference to this object in its ``data``
    attribute, so the instance lives as long as any node does.

    Build it with :meth:`from_p` or :meth:`from_instance`; calling the
    class directly gives an uninitialized object.

    Attributes
    ----------
    p : list[list[int]]
        Copy of the processing times for each job (row) on each
        machine (column). Treat as read-only.

    edges : list[tuple[int, int]]
        Copy of the machine-precedence edges. Treat as read-only.
    """

    @classmethod
    def from_p(cls, p, edges=None):
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
        cdef:
            FlowShopInstanceData out
            MachineGraph mach_graph
            vector[vector[int]] p_
            int m

        if not p:
            raise ValueError('p must contain at least one job')
        m = len(p[0])
        for j, row in enumerate(p):
            if len(row) != m:
                raise ValueError(
                    f'Row {j} of p has {len(row)} processing times;'
                    f' expected {m}'
                )

        # Create sequential MachineGraph by default
        if edges is None:
            edges = [(i, i + 1) for i in range(m - 1)]
        mi = MachGraphInterface.from_edges(edges)
        if mi.M != m:
            raise ValueError(
                f'p has {m} machines (columns) but the machine graph'
                f' has {mi.M}'
            )

        out = cls.__new__(cls)
        out.p = [list(row) for row in p]
        out.edges = [tuple(e) for e in edges]
        p_ = out.p
        mach_graph = create_machine_graph(mi)
        out._data.reset(new InstanceData(p_, mach_graph))
        return out

    @classmethod
    def from_instance(cls, instance):
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
        return cls.from_p(instance.p, instance.edges)

    def to_instance(self):
        """Export as an ``AssemblyFlowShopInstance``.

        Returns
        -------
        AssemblyFlowShopInstance
            Instance with copies of ``p`` and ``edges``
        """
        from bnbprob.pafssp.instances import AssemblyFlowShopInstance

        self._checked_ptr()
        return AssemblyFlowShopInstance(
            [list(row) for row in self.p], list(self.edges)
        )

    @property
    def n(self):
        """Number of jobs"""
        return deref(self._checked_ptr()).get_n()

    @property
    def m(self):
        """Number of machines"""
        return deref(self._checked_ptr()).get_m()

    @property
    def mach_graph(self):
        """Machine graph (Python copy of the C++ graph)"""
        cdef:
            MachineGraph mg_cpp
        mg_cpp = deref(self._checked_ptr()).get_mach_graph()
        return get_mach_graph(mg_cpp)

    def __repr__(self) -> str:
        if self.ptr() == NULL:
            return 'FlowShopInstanceData (uninitialized)'
        return (
            f'FlowShopInstanceData(n={self.n}, m={self.m},'
            f' edges={self.edges})'
        )

    def __reduce__(self):
        self._checked_ptr()
        return (_rebuild, (type(self), self.p, self.edges))

    cdef const InstanceData* _checked_ptr(FlowShopInstanceData self) except NULL:
        if self._data.get() == NULL:
            raise ReferenceError(INIT_ERROR)
        return self._data.get()
