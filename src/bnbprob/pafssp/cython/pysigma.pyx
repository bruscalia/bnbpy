# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False

from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.memory cimport make_shared, shared_ptr

from cython.operator cimport dereference as deref

from bnbprob.pafssp.cpp.environ cimport Sigma, Job, JobPtr, MachineGraph
from bnbprob.pafssp.cython.utils cimport create_machine_graph, get_mach_graph
from bnbprob.pafssp.cython.pyjob cimport PyJob, job_to_py
from bnbprob.pafssp.machinegraph import MachineGraph as MachGraphInterface

INIT_ERROR = 'C++ Sigma not initialized'


cdef class PySigma:

    def __cinit__(self):
        self._initialized = False

    def __repr__(self) -> str:
        return self._signature

    def __str__(self) -> str:
        return self._signature

    @property
    def _signature(self):
        if not self._initialized:
            return 'Sigma (uninitialized)'
        return f'Sigma(m={self.m}, jobs={len(self.jobs)})'

    @property
    def m(self):
        return self.get_m()

    @property
    def jobs(self):
        return self.get_jobs()

    @property
    def C(self):
        return self.get_C()

    @staticmethod
    def empty(int m, edges=None):
        """Create an empty Sigma with given number of machines and machine graph edges."""
        cdef:
            MachineGraph mach_graph
            PySigma out

        out = PySigma.__new__(PySigma)

        # Create sequential MachineGraph if no edges provided
        if edges is None:
            edges = [(i, i + 1) for i in range(m - 1)]

        mi = MachGraphInterface.from_edges(edges)
        mach_graph = create_machine_graph(mi)
        out.mach_graph = mach_graph

        # Create empty Sigma
        out.sigma = Sigma(m, &out.mach_graph)
        out._initialized = True
        return out

    @staticmethod
    def from_jobs(int m, list[PyJob] jobs, edges=None):
        """Create Sigma from list of PyJob objects."""
        cdef:
            MachineGraph mach_graph
            vector[shared_ptr[Job]] job_ptrs
            PySigma out
            PyJob py_job
            JobPtr job_ptr

        out = PySigma.__new__(PySigma)

        # Create sequential MachineGraph if no edges provided
        if edges is None:
            edges = [(i, i + 1) for i in range(m - 1)]

        mi = MachGraphInterface.from_edges(edges)
        mach_graph = create_machine_graph(mi)
        out.mach_graph = mach_graph

        # Create sigma and later push jobs
        out.sigma = Sigma(m, job_ptrs, &out.mach_graph)

        # Convert PyJob objects to C++ Job shared_ptrs
        for job in jobs:
            if isinstance(job, PyJob):
                py_job = <PyJob>job
                job_ptr = py_job.get_jobptr()
                if job_ptr != NULL:
                    out.sigma.job_to_bottom(job_ptr)
                else:
                    raise ValueError("PyJob not properly initialized")
            else:
                raise TypeError("All jobs must be PyJob instances")

        # Finally set initialized
        out._initialized = True
        return out

    cdef void _push_to_bottom(self, PyJob job):
        cdef JobPtr job_ptr = job.get_jobptr()
        if job_ptr == NULL:
            raise ValueError("PyJob not properly initialized")
        self.sigma.job_to_bottom(job_ptr)

    cdef void _push_to_top(self, PyJob job):
        cdef JobPtr job_ptr = job.get_jobptr()
        if job_ptr == NULL:
            raise ValueError("PyJob not properly initialized")
        self.sigma.job_to_top(job_ptr)

    cpdef void push_to_bottom(self, PyJob job):
        if not self._initialized:
            raise ReferenceError(INIT_ERROR)
        self._push_to_bottom(job)

    cpdef void push_to_top(self, PyJob job):
        if not self._initialized:
            raise ReferenceError(INIT_ERROR)
        self._push_to_top(job)

    cpdef int get_m(self):
        if not self._initialized:
            raise ReferenceError(INIT_ERROR)
        return self.sigma.m

    cpdef list get_jobs(self):
        cdef:
            list[PyJob] out
            unsigned int i

        if not self._initialized:
            raise ReferenceError(INIT_ERROR)

        out = []
        for i in range(self.sigma.jobs.size()):
            if self.sigma.jobs[i] != NULL:
                out.append(job_to_py(self.sigma.jobs[i]))
        return out

    cpdef list[int] get_C(self):
        cdef:
            list[int] out
            unsigned int i

        if not self._initialized:
            raise ReferenceError(INIT_ERROR)

        out = []
        for i in range(self.sigma.C.size()):
            out.append(self.sigma.C[i])
        return out

    def get_mach_graph(self):
        if not self._initialized:
            raise ReferenceError(INIT_ERROR)

        # For now, return a simple representation
        # This could be enhanced to return a proper MachGraphInterface object
        cdef:
            MachineGraph mg_cpp
            object mg
        mg_cpp = self.sigma.get_mach_graph()
        mg = get_mach_graph(mg_cpp)
        return mg

    cdef bool _is_empty(self):
        return self.sigma.jobs.size() == 0

    cdef size_t _size(self):
        return self.sigma.jobs.size()

    def is_empty(self):
        if not self._initialized:
            raise ReferenceError(INIT_ERROR)
        return self._is_empty()

    def size(self):
        if not self._initialized:
            raise ReferenceError(INIT_ERROR)
        return self._size()


cdef PySigma sigma_to_py(Sigma sigma):
    cdef:
        PySigma py_sigma

    py_sigma = PySigma.__new__(PySigma)
    py_sigma.sigma = sigma
    py_sigma.mach_graph = sigma.get_mach_graph()
    py_sigma._initialized = True
    return py_sigma
