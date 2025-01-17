# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp.vector cimport vector
from libcpp.memory cimport make_shared

from cython.operator cimport dereference as deref

from bnbprob.pfssp.cpp.job cimport Job, JobPtr

INIT_ERROR = 'C++ Job shared pointer not initialized'


cdef class PyJob:

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

    @property
    def slope(self):
        return self.get_slope()

    @staticmethod
    def from_p(int j, list[int] p):
        cdef:
            int N, i
            vector[int] p_
            PyJob out

        out = PyJob.__new__(PyJob)
        p_ = p
        out.job = make_shared[Job](j, p_)
        return out

    cpdef int get_j(self) except *:
        if self.job == NULL:
            raise ReferenceError(INIT_ERROR)
        return deref(self.job).j

    cpdef list[int] get_p(self) except *:
        cdef:
            int i, pi
            list[int] out
        if self.job == NULL:
            raise ReferenceError(INIT_ERROR)
        out = []
        for i in range(deref(deref(self.job).p).size()):
            pi = deref(deref(self.job).p)[i]
            out.append(pi)
        return out

    cpdef list[int] get_r(self) except *:
        cdef:
            int i, ri
            list[int] out
        if self.job == NULL:
            raise ReferenceError(INIT_ERROR)
        out = []
        for i in range(deref(self.job).r.size()):
            ri = deref(self.job).r[i]
            out.append(ri)
        return out

    cpdef list[int] get_q(self) except *:
        cdef:
            int i, qi
            list[int] out
        if self.job == NULL:
            raise ReferenceError(INIT_ERROR)
        out = []
        for i in range(deref(self.job).q.size()):
            qi = deref(self.job).q[i]
            out.append(qi)
        return out

    cpdef list[int] get_lat(self) except *:
        cdef:
            int i, j, li
            list[int] lati
            list[list[int]] out
        if self.job == NULL:
            raise ReferenceError(INIT_ERROR)
        out = []
        for i in range(deref(deref(self.job).lat).size()):
            out.append([])
            for j in range(deref(deref(self.job).lat)[i].size()):
                li = deref(deref(self.job).lat)[i][j]
                out[i].append(li)
        return out

    cpdef int get_slope(self) except *:
        if self.job == NULL:
            raise ReferenceError(INIT_ERROR)
        return deref(self.job).slope

    cpdef int get_T(self) except *:
        if self.job == NULL:
            raise ReferenceError(INIT_ERROR)
        return deref(self.job).T


cdef PyJob job_to_py(JobPtr& jobptr) except *:
    cdef:
        PyJob out
    if jobptr == NULL:
        raise ReferenceError(INIT_ERROR)
    out = PyJob.__new__(PyJob)
    out.job = jobptr
    return out
