# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from bnbprob.pafssp.cpp.environ cimport Sigma, MachineGraph
from bnbprob.pafssp.cython.pyjob cimport PyJob


cdef class PySigma:
    cdef:
        Sigma sigma
        MachineGraph mach_graph
        bool _initialized

    # Public cpdef methods (accessible from both Python and Cython)
    cpdef int get_m(self)
    cpdef list get_jobs(self)
    cpdef list[int] get_C(self)

    # Internal cdef methods (C-only, faster)
    cdef void _push_to_bottom(self, PyJob job)
    cdef void _push_to_top(self, PyJob job)
    cpdef void push_to_bottom(self, PyJob job)
    cpdef void push_to_top(self, PyJob job)
    cdef bool _is_empty(self)
    cdef size_t _size(self)


cdef PySigma sigma_to_py(Sigma sigma)
