# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp.vector cimport vector

from bnbprob.pafssp.cpp.environ cimport MachineGraph

cdef MachineGraph create_machine_graph(object mi)

cdef object get_mach_graph(MachineGraph& mg_cpp)
