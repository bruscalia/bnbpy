# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

from libcpp.memory cimport unique_ptr

from bnbprob.pafssp.cpp.environ cimport InstanceData


cdef class FlowShopInstanceData:

    cdef:
        unique_ptr[InstanceData] _data
        readonly list p
        readonly list edges
        object __weakref__

    cdef inline const InstanceData* ptr(FlowShopInstanceData self):
        return self._data.get()

    cdef const InstanceData* _checked_ptr(FlowShopInstanceData self) except NULL
