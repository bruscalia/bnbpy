# distutils: language = c++
# cython: language_level=3str, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.string cimport string
from cython.operator cimport dereference as deref

import logging
from typing import Literal

from bnbprob.pafssp.cpp.environ cimport (
    InstanceData,
    JobPtr,
    Permutation,
    iga,
    intensify,
    local_search,
    neh_initialization,
    quick_constructive,
    randomized_heur
)
from bnbprob.pafssp.cython.instance cimport FlowShopInstanceData
from bnbprob.pafssp.cython.pyjob cimport PyJob, job_to_py
from bnbprob.pafssp.cython.pysigma cimport PySigma, sigma_to_py
from bnbpy.cython.problem cimport Problem
from bnbpy.cython.solution cimport Solution


cdef:
    int DEFAULT_SEED = 42


cdef class PermFlowShop(Problem):
    """
    Class to represent a permutation flow-shop scheduling problem
    with lower bounds computed by the max of a single machine and
    a two machine relaxations.

    The bounds for single and two-machine problems are described
    by Potts (1980), also implemented by Ladhari & Haouari (2005),
    therein described as 'LB1' and 'LB5'.

    The `constructive` attribute selects the warmstart strategy:
    'neh' uses Nawaz et al. (1983), 'quick' uses the slope-sorting
    heuristic by Palmer (1965), 'multistart' applies randomized
    multi-iteration NEH, and 'iga' uses the Iterated Greedy Algorithm
    by Ruiz & Stützle (2007).

    Attributes
    ----------
    data : FlowShopInstanceData
        Instance data shared by all nodes of the same problem
        (read-only).

    Notes
    -----
    Lifetime: the root is created with :meth:`from_p`, or as
    ``PermFlowShop(data)`` with ``data`` from :meth:`create_data`.
    Every node (root, children, and heuristic solutions) keeps a reference
    to the same :class:`FlowShopInstanceData` in its ``data`` attribute,
    which owns
    the jobs and the machine graph, so any node stays valid after the
    root is garbage-collected. A bare ``PermFlowShop()`` has
    ``data = None`` and is only a placeholder.

    References
    ----------
    Ladhari, T., & Haouari, M. (2005). A computational study of
    the permutation flow shop problem based on a tight lower bound.
    Computers & Operations Research, 32(7), 1831-1847.

    Nawaz, M., Enscore Jr, E. E., & Ham, I. (1983).
    A heuristic algorithm for the m-machine,
    n-job flow-shop sequencing problem.
    Omega, 11(1), 91-95.

    Palmer, D. S. (1965). Sequencing jobs through a multi-stage process
    in the minimum total time—a quick method of obtaining a near optimum.
    Journal of the Operational Research Society, 16(1), 101-107.

    Potts, C. N. (1980). An adaptive branching rule for the permutation
    flow-shop problem. European Journal of Operational Research, 5(1), 19-25.

    Ruiz, R., & Stützle, T. (2007). A simple and effective iterated
    greedy algorithm for the permutation flowshop scheduling problem.
    European Journal of Operational Research, 177(3), 2033-2049.
    """

    def __init__(
        self,
        FlowShopInstanceData data=None,
        constructive: Literal['neh', 'quick', 'multistart', 'iga'] = 'neh',
    ) -> None:
        """Instantiate the root problem.

        Parameters
        ----------
        data : Optional[FlowShopInstanceData], optional
            Instance data, built with :meth:`create_data`,
            ``FlowShopInstanceData.from_p`` or
            ``FlowShopInstanceData.from_instance``. By default None,
            which gives a placeholder that cannot be solved.

        constructive : Literal['neh', 'quick', 'multistart', 'iga']
            Constructive heuristic, by default 'neh'

        Raises
        ------
        ValueError
            If ``data`` is an uninitialized ``FlowShopInstanceData``
        """
        self.solution = Solution()
        self.constructive = <string> constructive.encode("utf-8")
        self.simple_upgraded = False
        if data is not None:
            if data.ptr() == NULL:
                raise ValueError(
                    'data must be an initialized FlowShopInstanceData'
                )
            self.set_data(data)

    @staticmethod
    def create_data(p, edges=None):
        """Build instance data from processing times and machine-graph
        edges, to be passed to the constructor.

        Shortcut for ``FlowShopInstanceData.from_p(p, edges)``.

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
        return FlowShopInstanceData.from_p(p, edges)

    @classmethod
    def from_p(
        cls,
        p,
        edges=None,
        constructive: Literal['neh', 'quick', 'multistart', 'iga'] = 'neh',
    ):
        """Instantiate the root problem from processing times and
        machine-graph edges.

        Builds new instance data for this root, shared by all nodes
        derived from it. To build several roots on the same data, use
        ``cls(data)`` with ``data`` from :meth:`create_data`.

        Parameters
        ----------
        p : list[list[int]]
            Processing times for each job (row) on each machine (column)

        edges : Optional[list[tuple[int, int]]], optional
            Machine-precedence edges, by default None (sequential)

        constructive : Literal['neh', 'quick', 'multistart', 'iga']
            Constructive heuristic, by default 'neh'

        Returns
        -------
        PermFlowShop
            Root node of the problem (instance of ``cls``)

        Raises
        ------
        ValueError
            If ``p`` is empty, has rows of different lengths, or its
            number of columns differs from the number of machines in the
            graph. ``CyclicGraphError`` (a ``ValueError``) if the edges
            contain a cycle.
        """
        return cls(
            FlowShopInstanceData.from_p(p, edges), constructive=constructive
        )

    @classmethod
    def from_data(
        cls,
        FlowShopInstanceData data,
        constructive: Literal['neh', 'quick', 'multistart', 'iga'] = 'neh',
    ):
        """Instantiate the root problem from instance data.

        Equivalent to ``cls(data, constructive)``, except that ``data``
        is required.

        Parameters
        ----------
        data : FlowShopInstanceData
            Instance data, built with :meth:`create_data`,
            ``FlowShopInstanceData.from_p`` or
            ``FlowShopInstanceData.from_instance``

        constructive : Literal['neh', 'quick', 'multistart', 'iga']
            Constructive heuristic, by default 'neh'

        Returns
        -------
        PermFlowShop
            Root node of the problem (instance of ``cls``)

        Raises
        ------
        ValueError
            If ``data`` is None or uninitialized
        """
        if data is None:
            raise ValueError(
                'data must be an initialized FlowShopInstanceData'
            )
        return cls(data, constructive=constructive)

    @property
    def sequence(self):
        """Get the current job sequence with start times.

        Start times are computed on export. For partial permutations
        they follow ``sigma1 + free_jobs (current order) + sigma2``.
        """
        cdef:
            size_t i
            vector[JobPtr] seq
            vector[vector[int]] starts
            PyJob job
        out = []
        seq = self.perm.get_sequence()
        starts = self.perm.compute_starts()
        for i in range(seq.size()):
            job = job_to_py(seq[i])
            job.s = starts[i]
            out.append(job)
        return out

    @property
    def free_jobs(self):
        """Get the list of free (unscheduled) jobs, without start times"""
        cdef:
            int i
            vector[JobPtr] seq
            PyJob job
        out = []
        seq = self.perm.get_free_jobs()
        for i in range(seq.size()):
            job = job_to_py(seq[i])
            out.append(job)
        return out

    @property
    def sigma1(self):
        cdef:
            PySigma py_sigma
        py_sigma = sigma_to_py(self.perm.sigma1)
        return py_sigma

    @property
    def sigma2(self):
        cdef:
            PySigma py_sigma
        py_sigma = sigma_to_py(self.perm.sigma2)
        return py_sigma

    cpdef object get_mach_graph(PermFlowShop self):
        self._inst()
        return self.data.mach_graph

    cpdef PermFlowShop warmstart(PermFlowShop self):
        if self.constructive == 'neh':
            return self.neh_initialization()
        elif self.constructive == 'multistart':
            return self.multistart_initialization()
        elif self.constructive == 'iga':
            return self.iga_initialization()
        return self.quick_constructive()

    cpdef PermFlowShop quick_constructive(PermFlowShop self):
        cdef:
            PermFlowShop child
            Permutation perm
            vector[JobPtr] jobs
            const InstanceData* inst = self._inst()

        jobs = self.perm.get_sequence()
        perm = quick_constructive(jobs, deref(inst))
        child = self._copy()
        child.perm = perm
        return child

    cpdef PermFlowShop neh_initialization(PermFlowShop self):
        cdef:
            PermFlowShop child
            Permutation perm
            vector[JobPtr] jobs
            const InstanceData* inst = self._inst()

        jobs = self.perm.get_sequence()
        perm = neh_initialization(jobs, deref(inst))
        child = self._copy()
        child.perm = perm
        return child

    cpdef PermFlowShop multistart_initialization(PermFlowShop self):
        cdef:
            int n_iter, n_jobs, n_machines
            PermFlowShop child
            Permutation perm
            vector[JobPtr] jobs
            const InstanceData* inst = self._inst()

        jobs = self.perm.get_sequence()
        n_jobs = jobs.size()
        if n_jobs > 0:
            n_machines = deref(inst).get_m()
            n_iter = n_jobs * n_machines
        else:
            n_iter = 0
        perm = randomized_heur(jobs, n_iter, DEFAULT_SEED, deref(inst))
        child = self._copy()
        child.perm = perm
        return child

    cpdef PermFlowShop iga_initialization(PermFlowShop self):
        cdef:
            int n_jobs, n_iter, n_machines, d
            Permutation perm
            PermFlowShop sol_alt, neh_sol
            vector[JobPtr] jobs
            const InstanceData* inst = self._inst()

        neh_sol = self.neh_initialization()
        jobs = neh_sol.perm.get_sequence()
        n_jobs = jobs.size()
        if n_jobs > 0:
            n_machines = deref(inst).get_m()
            n_iter = n_jobs * n_machines
        else:
            n_iter = 0
        d = max(5, n_jobs // 10)
        perm = iga(jobs, deref(inst), n_iter, d, DEFAULT_SEED)
        sol_alt = self._copy()
        sol_alt.perm = perm
        sol_alt.solution.set_feasible()
        sol_alt.solution.set_lb(perm.calc_lb_full())
        return sol_alt

    cpdef PermFlowShop local_search(PermFlowShop self):
        cdef:
            double lb, new_cost
            Permutation perm
            PermFlowShop sol_alt
            vector[JobPtr] jobs
            const InstanceData* inst = self._inst()

        lb = self.solution.lb
        jobs = self.perm.get_sequence()
        perm = local_search(jobs, deref(inst))
        new_cost = perm.calc_lb_full()
        if new_cost < lb:
            sol_alt = self._copy()
            sol_alt.perm = perm
            sol_alt.solution.set_feasible()
            sol_alt.solution.set_lb(new_cost)
            return sol_alt
        return None

    cpdef PermFlowShop randomized_heur(PermFlowShop self, int n_iter, unsigned int seed=0):
        cdef:
            Permutation perm
            PermFlowShop sol_alt
            vector[JobPtr] jobs
            const InstanceData* inst = self._inst()

        jobs = self.perm.get_sequence()
        perm = randomized_heur(jobs, n_iter, seed, deref(inst))
        sol_alt = self._copy()
        sol_alt.perm = perm
        sol_alt.solution.set_feasible()
        sol_alt.solution.set_lb(perm.calc_lb_full())
        return sol_alt

    cpdef PermFlowShop iga_heur(PermFlowShop self, int n_iter, int d, unsigned int seed=0):
        cdef:
            Permutation perm
            PermFlowShop sol_alt
            vector[JobPtr] jobs
            const InstanceData* inst = self._inst()

        jobs = self.neh_initialization().perm.get_sequence()
        perm = iga(jobs, deref(inst), n_iter, d, seed)
        sol_alt = self._copy()
        sol_alt.perm = perm
        sol_alt.solution.set_feasible()
        sol_alt.solution.set_lb(perm.calc_lb_full())
        return sol_alt

    cpdef PermFlowShop intensify(
        PermFlowShop self,
        PermFlowShop reference
    ):
        cdef:
            double new_cost, lb
            PermFlowShop sol_alt

        # Both permutations must point into the same InstanceData
        self._inst()
        if reference.data is not self.data:
            raise ValueError(
                'reference must share the same FlowShopInstanceData'
            )
        sol_alt = self._copy()
        sol_alt.perm = intensify(
            self.perm,
            reference.perm
        )
        new_cost = sol_alt.perm.calc_lb_full()
        sol_alt.solution.set_lb(new_cost)
        sol_alt.solution.set_feasible()

        return sol_alt

    cpdef double calc_bound(PermFlowShop self):
        return self.perm.calc_lb_1m()

    cpdef bool is_feasible(PermFlowShop self):
        return self.perm.is_feasible()

    cpdef list[PermFlowShop] branch(PermFlowShop self):
        # Get fixed and unfixed job lists to create new solution
        cdef:
            int j, J
            list[PermFlowShop] out

        J = self.perm.free_jobs.size()
        out = [None] * J
        for j in range(J):
            out[j] = self._child_push(j)
        return out

    cpdef double stronger_bound(PermFlowShop self):
        if self.perm.free_jobs.size() == 0:
            return <double>self.perm.calc_lb_full()

        if self.simple_upgraded:
            return <double>self.perm.lower_bound_2m()

        self.simple_upgraded = True
        self.perm.update_params()
        return <double>self.perm.lower_bound_1m()

    cpdef PermFlowShop primal_heuristic(PermFlowShop self):
        return self.local_search()

    cdef PermFlowShop _child_push(PermFlowShop self, int& j):
        cdef:
            PermFlowShop child = self._copy()

        child._push_job(j)
        return child

    cpdef int calc_lb_1m(PermFlowShop self):
        return self.perm.calc_lb_1m()

    cpdef int calc_lb_2m(PermFlowShop self):
        return self.perm.calc_lb_2m()

    cpdef int lower_bound_1m(PermFlowShop self):
        return self.perm.lower_bound_1m()

    cpdef int lower_bound_2m(PermFlowShop self):
        return self.perm.lower_bound_2m()

    cpdef void update_params(PermFlowShop self):
        self.perm.update_params()

    cpdef void push_job(PermFlowShop self, int& j):
        self.perm.push_job(j)

    cdef void _push_job(PermFlowShop self, int& j):
        self.perm.push_job(j)

    cpdef int calc_idle_time(PermFlowShop self):
        return self.perm.calc_idle_time()

    cpdef int calc_tot_time(PermFlowShop self):
        return self.perm.calc_tot_time()

    cpdef PermFlowShop copy(PermFlowShop self, bool deep=False):
        return self._copy()

    cdef PermFlowShop _copy(PermFlowShop self):
        cdef:
            PermFlowShop child
        child = PermFlowShop.__new__(PermFlowShop)
        child.solution = Solution()
        child.constructive = self.constructive
        child.data = self.data
        child.perm = self.perm
        child.simple_upgraded = False
        return child


cdef class BenchPermFlowShop(PermFlowShop):
    """Benchmarking variant of PermFlowShop.

    ``calc_bound`` always calls ``update_params()`` before computing the
    single-machine bound, so that parameter update cost is included in
    timing measurements.
    """

    cpdef double calc_bound(BenchPermFlowShop self):
        self.perm.update_params()
        return self.perm.calc_lb_1m()

    cdef BenchPermFlowShop _copy(BenchPermFlowShop self):
        cdef:
            BenchPermFlowShop child
        child = BenchPermFlowShop.__new__(BenchPermFlowShop)
        child.solution = Solution()
        child.constructive = self.constructive
        child.data = self.data
        child.perm = self.perm
        child.simple_upgraded = False
        return child


cdef class PermFlowShop1M(PermFlowShop):
    """Variant of PermFlowShop that only ever applies the single-machine
    bound upgrade. The two-machine bound (LB5) is never computed, which
    reduces per-node cost at the expense of a looser bound.
    """

    cpdef double calc_bound(PermFlowShop1M self):
        return self.perm.calc_lb_1m()

    cdef PermFlowShop1M _copy(PermFlowShop1M self):
        cdef:
            PermFlowShop1M child
        child = PermFlowShop1M.__new__(PermFlowShop1M)
        child.solution = Solution()
        child.constructive = self.constructive
        child.data = self.data
        child.perm = self.perm
        child.simple_upgraded = False
        return child
