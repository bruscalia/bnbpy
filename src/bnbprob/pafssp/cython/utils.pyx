# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp.vector cimport vector
from libcpp.memory cimport shared_ptr

from bnbprob.pafssp.cpp.environ cimport MachineGraph
from bnbprob.pafssp.machinegraph import MachineGraph as MachGraphInterface


cdef MachineGraph create_machine_graph(object mi):
    cdef:
        int M
        vector[vector[int]] prec
        vector[vector[int]] succ
        vector[int] topo_order
        vector[int] rev_topo_order
        vector[vector[int]] descendants
        int i, j

    # Extract attributes from Python MachineGraph
    M = mi.M

    # Convert precedence relationships
    prec.resize(M)
    for i in range(M):
        for j in mi.prec[i]:
            prec[i].push_back(j)

    # Convert successor relationships
    succ.resize(M)
    for i in range(M):
        for j in mi.succ[i]:
            succ[i].push_back(j)

    # Convert topological order
    topo_order.resize(len(mi.topo_order))
    for i in range(len(mi.topo_order)):
        topo_order[i] = mi.topo_order[i]

    # Convert reverse topological order
    rev_topo_order.resize(len(mi.rev_topo_order))
    for i in range(len(mi.rev_topo_order)):
        rev_topo_order[i] = mi.rev_topo_order[i]

    # Convert descendants
    descendants.resize(len(mi.descendants))
    for i in range(len(mi.descendants)):
        descendants[i].resize(len(mi.descendants[i]))
        for j in range(len(mi.descendants[i])):
            descendants[i][j] = mi.descendants[i][j]

    # Create and return C++ MachineGraph
    return MachineGraph(M, prec, succ, topo_order, rev_topo_order, descendants)


cdef object get_mach_graph(MachineGraph& mg_cpp):
    cdef:
        int m
        vector[vector[int]] prec
        vector[vector[int]] succ
        vector[int] topo_order
        vector[int] rev_topo_order
        vector[vector[int]] descendants

    prec = mg_cpp.get_prec_all()
    succ = mg_cpp.get_succ_all()
    topo_order = mg_cpp.get_topo_order()
    rev_topo_order = mg_cpp.get_rev_topo_order()
    descendants = mg_cpp.get_descendants()
    m = topo_order.size()

    mg = MachGraphInterface(
        m,
        prec,
        succ,
        topo_order,
        rev_topo_order,
        descendants
    )

    return mg
