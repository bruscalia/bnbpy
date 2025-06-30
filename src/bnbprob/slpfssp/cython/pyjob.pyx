# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp.vector cimport vector
from libcpp.memory cimport make_shared

from cython.operator cimport dereference as deref

from bnbprob.slpfssp.cpp.environ cimport Job, JobPtr

INIT_ERROR = 'C++ Job shared pointer not initialized'


cdef class PyJob:

    def __repr__(self) -> str:
        return self._signature

    def __str__(self) -> str:
        return self._signature

    @property
    def _signature(self):
        return f'Job {self.j}'

    @property
    def j(self):
        return self.get_j()

    @property
    def p(self):
        return self.get_p()

    @property
    def r(self):
        return self.get_r()

    @property
    def q(self):
        return self.get_q()

    @property
    def lat(self):
        return self.get_lat()

    @property
    def T(self):
        return self.get_T()

    @staticmethod
    def from_p(int j, list[list[int]] p):
        cdef:
            int N, i
            vector[vector[int]] p_
            PyJob out

        out = PyJob.__new__(PyJob)
        p_ = p
        out.job = make_shared[Job](j, p_)
        return out

    cpdef int get_j(self):
        if self.job == NULL:
            raise ReferenceError(INIT_ERROR)
        return deref(self.job).j

    cpdef list[list[int]] get_p(self):
        cdef:
            list[list[int]] out
        if self.job == NULL:
            raise ReferenceError(INIT_ERROR)
        out = deref(deref(self.job).p)
        return out

    cpdef list[list[int]] get_r(self):
        cdef:
            list[list[int]] out
        if self.job == NULL:
            raise ReferenceError(INIT_ERROR)
        out = deref(self.job).r
        return out

    cpdef list[list[int]] get_q(self):
        cdef:
            list[list[int]] out
        if self.job == NULL:
            raise ReferenceError(INIT_ERROR)
        out = deref(self.job).q
        return out

    cpdef list[list[list[int]]] get_lat(self):
        cdef:
            list[list[list[int]]] out
        if self.job == NULL:
            raise ReferenceError(INIT_ERROR)
        out = deref(deref(self.job).lat)
        return out

    cpdef int get_T(self):
        cdef:
            int out
        if self.job == NULL:
            raise ReferenceError(INIT_ERROR)
        out = deref(self.job).get_T()
        return out


cdef PyJob job_to_py(JobPtr& jobptr):
    cdef:
        PyJob out
    if jobptr == NULL:
        raise ReferenceError(INIT_ERROR)
    out = PyJob.__new__(PyJob)
    out.job = jobptr
    return out
