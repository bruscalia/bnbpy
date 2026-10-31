# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

from libcpp cimport bool
from libcpp.string cimport string
from libcpp.vector cimport vector

from bnbprob.pafssp.cpp.environ cimport InstanceData, Permutation
from bnbprob.pafssp.cython.instance cimport FlowShopInstanceData
from bnbpy.cython.problem cimport Problem
from bnbpy.cython.solution cimport Solution


cdef class PermFlowShop(Problem):

    cdef public:
        string constructive
        bool simple_upgraded
        # Cannot override attribute `solution` in cdef class
        # due to Cython limitation

    cdef readonly:
        # Keeps the instance (jobs, graph) alive while this node exists
        FlowShopInstanceData data

    cdef:
        Permutation perm

    cdef inline void set_data(PermFlowShop self, FlowShopInstanceData data):
        self.data = data
        self.perm = Permutation(data.ptr())

    cdef inline const InstanceData* _inst(PermFlowShop self) except NULL:
        if self.data is None or self.data.ptr() == NULL:
            raise ValueError(
                'PermFlowShop has no instance data;'
                ' build it with PermFlowShop.from_p or PermFlowShop(data)'
            )
        return self.data.ptr()

    cdef inline Permutation get_perm(PermFlowShop self):
        return self.perm

    cdef inline int get_n(PermFlowShop self):
        return self.perm.n

    cpdef object get_mach_graph(PermFlowShop self)

    cpdef PermFlowShop warmstart(PermFlowShop self)

    cpdef PermFlowShop quick_constructive(PermFlowShop self)

    cpdef PermFlowShop neh_initialization(PermFlowShop self)

    cpdef PermFlowShop multistart_initialization(PermFlowShop self)

    cpdef PermFlowShop iga_initialization(PermFlowShop self)

    cpdef PermFlowShop local_search(PermFlowShop self)

    cpdef PermFlowShop randomized_heur(PermFlowShop self, int n_iter, unsigned int seed=*)

    cpdef PermFlowShop iga_heur(PermFlowShop self, int n_iter, int d, unsigned int seed=*)

    cpdef PermFlowShop intensify(
        PermFlowShop self,
        PermFlowShop reference
    )

    cpdef double calc_bound(PermFlowShop self)

    cpdef bool is_feasible(PermFlowShop self)

    cpdef list[PermFlowShop] branch(PermFlowShop self)

    cdef PermFlowShop _child_push(PermFlowShop self, int& j)

    cpdef double stronger_bound(PermFlowShop self)

    cpdef PermFlowShop primal_heuristic(PermFlowShop self)

    cpdef int calc_lb_1m(PermFlowShop self)

    cpdef int calc_lb_2m(PermFlowShop self)

    cpdef int lower_bound_1m(PermFlowShop self)

    cpdef int lower_bound_2m(PermFlowShop self)

    cpdef void update_params(PermFlowShop self)

    cpdef void push_job(PermFlowShop self, int& j)

    cdef void _push_job(PermFlowShop self, int& j)

    cpdef int calc_idle_time(PermFlowShop self)

    cpdef int calc_tot_time(PermFlowShop self)

    cpdef PermFlowShop copy(PermFlowShop self, bool deep=*)

    cdef PermFlowShop _copy(PermFlowShop self)


cdef class BenchPermFlowShop(PermFlowShop):

    cpdef double calc_bound(BenchPermFlowShop self)


cdef class PermFlowShop1M(PermFlowShop):

    cpdef double calc_bound(PermFlowShop1M self)
