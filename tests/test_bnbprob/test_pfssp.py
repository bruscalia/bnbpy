import dataclasses
import gc
import itertools
import json
import os
import pickle
import random
import weakref
from typing import Any, Callable, Optional, Type

import pytest

from bnbprob.pafssp import PyJob, PySigma
from bnbprob.pafssp.cython.bnb import (
    BenchCutoffBnB,
    CallbackBnB,
    CutoffBnB,
    LazyBnB,
)
from bnbprob.pafssp.cython.instance import FlowShopInstanceData
from bnbprob.pafssp.cython.problem import (
    BenchPermFlowShop,
    PermFlowShop,
    PermFlowShop1M,
)
from bnbprob.pafssp.instances import (
    AssemblyFlowShopInstance,
    random_parallel_semilines,
)
from bnbprob.pafssp.machinegraph import MachineGraph
from bnbpy.cython.search import (
    BestFirstBnB,
    BranchAndBound,
    BreadthFirstBnB,
    DepthFirstBnB,
)
from bnbpy.cython.status import OptStatus

HERE = os.path.dirname(os.path.abspath(__file__))
REGRESSION_PATH = os.path.join(
    HERE, os.pardir, 'instances', 'pafssp', 'regression.json'
)


def _load_regression() -> dict[str, Any]:
    with open(REGRESSION_PATH, encoding='utf8') as f:
        data: dict[str, Any] = json.load(f)
    return data


# Reference values captured from the implementation before the
# InstanceData refactor; the refactor must not change search behaviour
REGRESSION = _load_regression()
INSTANCES: dict[str, dict[str, Any]] = REGRESSION['instances']
EXPECTED: dict[str, Any] = REGRESSION['expected']
NAMES = list(INSTANCES)
CONSTRUCTIVES = ['neh', 'quick', 'multistart', 'iga']
PROBLEM_CLASSES: dict[str, Type[PermFlowShop]] = {
    'PermFlowShop': PermFlowShop,
    'PermFlowShop1M': PermFlowShop1M,
    'BenchPermFlowShop': BenchPermFlowShop,
}
SOLVERS: dict[str, Callable[[PermFlowShop], Any]] = {
    'LazyBnB': LazyBnB,
    'CallbackBnB': CallbackBnB,
    'DFS-in': lambda pr: DepthFirstBnB(pr, eval_node='in'),
    'BFS-out': lambda pr: BestFirstBnB(pr, eval_node='out'),
}


def _local_search_from_quick(root: PermFlowShop) -> Optional[PermFlowShop]:
    quick = root.quick_constructive()
    quick.compute_bound()
    return quick.local_search()


HEURISTICS: dict[str, Callable[[PermFlowShop], Optional[PermFlowShop]]] = {
    'randomized_heur': lambda root: root.randomized_heur(5, 7),
    'iga_heur': lambda root: root.iga_heur(10, 2, 7),
    'local_search': _local_search_from_quick,
    'intensify': lambda root: root.branch()[0].intensify(
        root.neh_initialization()
    ),
}


def make_data(name: str) -> FlowShopInstanceData:
    inst = INSTANCES[name]
    edges = [(e[0], e[1]) for e in inst['edges']]
    return FlowShopInstanceData.from_p(inst['p'], edges)


def make_root(
    name: str,
    cls: Type[PermFlowShop] = PermFlowShop,
    constructive: Any = 'neh',
) -> PermFlowShop:
    return cls.from_data(make_data(name), constructive=constructive)


def starts(sol: PermFlowShop) -> list[list[Any]]:
    return [[job.j, job.s] for job in sol.sequence]


def summary(sol: Optional[PermFlowShop]) -> Optional[dict[str, Any]]:
    if sol is None:
        return None
    return {
        'cost': sol.calc_lb_1m(),
        'order': [job.j for job in sol.sequence],
    }


def check_schedule(sol: PermFlowShop, name: str, cost: float) -> None:
    """Start times respect machine precedences within each job and the
    permutation on each machine, and their makespan is the cost."""
    p = INSTANCES[name]['p']
    edges = INSTANCES[name]['edges']
    m = len(p[0])
    seq = sol.sequence
    assert sorted(job.j for job in seq) == list(range(len(p)))
    for job in seq:
        assert len(job.s) == m
        for k1, k2 in edges:
            assert job.s[k2] >= job.s[k1] + job.p[k1]
    for prev, nxt in zip(seq, seq[1:]):
        for k in range(m):
            assert nxt.s[k] >= prev.s[k] + prev.p[k]
    makespan = max(job.s[k] + job.p[k] for job in seq for k in range(m))
    assert makespan == cost


@pytest.mark.pafssp
class TestPFSSP:
    J: int = 10
    M: int = 4
    p_choices: list[int] = list(range(5, 25))
    sol_value: int = 182
    nodes: int = 11

    @pytest.mark.parametrize(
        (
            'bnb_cls',
            'prob_cls',
            'eval_node',
            'cost',
            'explored',
            'constructive',
        ),
        [
            (DepthFirstBnB, PermFlowShop, 'in', 182, 11, 'quick'),
            (BestFirstBnB, PermFlowShop, 'in', 182, 11, 'quick'),
            (DepthFirstBnB, PermFlowShop, 'out', 182, 58, 'quick'),
            (BestFirstBnB, PermFlowShop, 'out', 182, 19, 'quick'),
            (DepthFirstBnB, PermFlowShop, 'in', 182, 0, 'neh'),
            (BestFirstBnB, PermFlowShop, 'in', 182, 0, 'neh'),
            (DepthFirstBnB, PermFlowShop, 'out', 182, 0, 'neh'),
            (BestFirstBnB, PermFlowShop, 'out', 182, 0, 'neh'),
        ],
    )
    def test_res_pfssp(  # noqa: PLR0913, PLR0917
        self,
        bnb_cls: Type[Any],
        prob_cls: Type[Any],
        eval_node: str,
        cost: int,
        explored: int,
        constructive: str,
    ) -> None:
        problem = self.start_problem(prob_cls, constructive=constructive)
        bnb = bnb_cls(problem, eval_node=eval_node)
        bnb.solve()
        cost_sol = bnb.solution.cost
        assert cost_sol == cost, (
            f'Wrong cost for FSSP {bnb_cls} {cost_sol}, expected {cost}'
        )
        assert bnb.explored == explored, (
            f'Wrong number of nodes explored for FSSP {bnb_cls}'
            f' {bnb.explored}, expected {explored}'
        )

    def start_problem(self, cls: Type[Any], **kwargs: Any) -> Any:
        random.seed(42)
        p: list[list[int]] = [
            [random.choice(self.p_choices) for _ in range(self.M)]
            for _ in range(self.J)
        ]
        problem = cls.from_data(FlowShopInstanceData.from_p(p), **kwargs)
        return problem

    def test_warmstart(self) -> None:
        problem = self.start_problem(PermFlowShop, constructive='quick')
        bnb = DepthFirstBnB(problem, eval_node='in')
        bnb.solve()
        cost: int = int(bnb.solution.cost)
        assert bnb.solution.cost == self.sol_value, (
            f'Wrong solution for DFS {cost}, expected {self.sol_value}'
        )
        assert bnb.explored == self.nodes, (
            f'Wrong number of explored nodes for DFS {bnb.explored},'
            f' expected {self.nodes}'
        )

    def test_lazy(
        self,
    ) -> None:
        problem = self.start_problem(PermFlowShop, constructive='quick')
        bnb = LazyBnB(problem, delay_lb5=False)
        bnb.solve()
        problem_lazy = self.start_problem(PermFlowShop)
        bnblazy = BranchAndBound(problem_lazy, eval_node='in')
        bnblazy.solve()
        base_cost: int = int(bnb.solution.cost)
        cb_cost: int = self.sol_value
        assert bnb.solution.cost == bnblazy.solution.cost, (
            f'Wrong solution for CB {base_cost}, expected {cb_cost}'
        )
        assert bnb.explored == self.nodes, (
            f'Wrong number of explored nodes for CB {bnblazy.explored},'
            f' expected {self.nodes}'
        )

    @staticmethod
    def test_neh() -> None:
        p: list[list[int]] = [
            [5, 9, 8, 10, 1],
            [9, 3, 10, 1, 8],
            [9, 4, 5, 8, 6],
            [4, 8, 8, 7, 2],
        ]
        res: int = 54
        data = FlowShopInstanceData.from_p(p)
        problem = PermFlowShop.from_data(data, constructive='neh')
        sol = problem.warmstart()
        cost: int = sol.calc_lb_1m()
        assert cost == res, f'Wrong result for neh {cost} vs 54 (expected)'


@pytest.mark.pafssp
class TestPFSSPBounds:
    p: list[list[int]] = [
        [5, 9, 7, 4],
        [9, 3, 3, 8],
        [8, 10, 5, 6],
        [1, 8, 6, 2],
    ]

    res_root: tuple[int, int] = (39, 42)
    res_first: list[tuple[int, int]] = [
        (43, 43),
        (47, 47),
        (46, 46),
        (39, 42),
    ]

    res_final: int = 43

    def test_root(self) -> None:
        problem = PermFlowShop.from_data(FlowShopInstanceData.from_p(self.p))
        lb1: int = problem.lower_bound_1m()
        lb5: int = problem.lower_bound_2m()
        assert (
            lb1,
            lb5,
        ) == self.res_root, (
            f'Wrong root lower bounds for toy problem: {(lb1, lb5)};'
            f' expected {self.res_root}'
        )

    @pytest.mark.parametrize('j', [0, 1, 2, 3])
    def test_first_level(self, j: int) -> None:
        problem = PermFlowShop.from_data(FlowShopInstanceData.from_p(self.p))
        problem.push_job(j)
        lb1: int = problem.lower_bound_1m()
        lb5: int = problem.lower_bound_2m()
        res: tuple[int, int] = self.res_first[j]
        assert (
            lb1,
            lb5,
        ) == res, (
            f'Wrong root lower bounds for toy problem: {(lb1, lb5)};'
            f' expected {res}'
        )

    def test_calc_tot_time(self) -> None:
        data = FlowShopInstanceData.from_p(self.p)
        root = PermFlowShop.from_data(data)
        # Nothing scheduled yet: all completion times are zero
        assert root.calc_tot_time() == 0

        sol = root.warmstart()
        expected = sum(sol.sigma1.C) + sum(sol.sigma2.C)
        assert expected > 0
        assert sol.calc_tot_time() == expected

    def test_calc_idle_time(self) -> None:
        data = FlowShopInstanceData.from_p(self.p)
        root = PermFlowShop.from_data(data)
        assert root.calc_idle_time() == 0

        # Complete solution: total time minus all processing times
        sol = root.warmstart()
        total_p = sum(map(sum, self.p))
        assert sol.calc_idle_time() == sol.calc_tot_time() - total_p


@pytest.mark.pafssp
class TestFlowShopInstanceData:
    p: list[list[int]] = [
        [5, 9, 7, 4],
        [9, 3, 3, 8],
        [8, 10, 5, 6],
    ]

    def test_from_p_defaults(self) -> None:
        p = [list(row) for row in self.p]
        data = FlowShopInstanceData.from_p(p)
        assert data.n == len(p)
        assert data.m == len(p[0])
        assert data.edges == [(0, 1), (1, 2), (2, 3)]
        assert data.p == p
        # Stored as copies of the input
        p[0][0] = 100
        assert data.p == self.p

    @staticmethod
    def test_mach_graph() -> None:
        data = make_data('ASM')
        edges = [(e[0], e[1]) for e in INSTANCES['ASM']['edges']]
        assert data.mach_graph == MachineGraph.from_edges(edges)
        problem = PermFlowShop.from_data(data)
        assert problem.get_mach_graph() == data.mach_graph

    @staticmethod
    def test_instance_round_trip() -> None:
        inst = random_parallel_semilines(8, (3, 3), seed=4)
        data = FlowShopInstanceData.from_instance(inst)
        assert data.n == len(inst.p)
        assert data.m == len(inst.p[0])
        out = data.to_instance()
        assert isinstance(out, AssemblyFlowShopInstance)
        assert out == inst
        assert out.p is not data.p

    @staticmethod
    @pytest.mark.parametrize(
        ('p', 'edges'),
        [
            ([], None),
            ([[1, 2], [3]], None),
            ([[1, 2], [4, 5]], [(0, 2)]),
            ([[1, 2], [3, 4]], [(0, 1), (1, 0)]),
        ],
        ids=['empty', 'ragged', 'edge-beyond-width', 'cyclic'],
    )
    def test_validation(
        p: list[list[int]], edges: Optional[list[tuple[int, int]]]
    ) -> None:
        with pytest.raises(ValueError):  # noqa: PT011
            FlowShopInstanceData.from_p(p, edges)

    @staticmethod
    def test_uninitialized() -> None:
        data = FlowShopInstanceData()
        assert 'uninitialized' in repr(data)
        with pytest.raises(ReferenceError):
            _ = data.n
        with pytest.raises(ReferenceError):
            _ = data.m
        with pytest.raises(ReferenceError):
            _ = data.mach_graph
        with pytest.raises(ReferenceError):
            data.to_instance()
        with pytest.raises(ReferenceError):
            pickle.dumps(data)
        with pytest.raises(ValueError, match='initialized'):
            PermFlowShop(data)
        with pytest.raises(ValueError, match='initialized'):
            PermFlowShop.from_data(data)
        with pytest.raises(ValueError, match='initialized'):
            PermFlowShop.from_data(None)  # type: ignore[arg-type]

    @staticmethod
    def test_pickle() -> None:
        data = make_data('DPM')
        clone = pickle.loads(pickle.dumps(data))
        assert isinstance(clone, FlowShopInstanceData)
        assert clone is not data
        assert clone.p == data.p
        assert clone.edges == data.edges
        expected = EXPECTED['DPM|warmstart|neh']['cost']
        assert PermFlowShop.from_data(clone).warmstart().calc_lb_1m() == (
            expected
        )

    def test_repr(self) -> None:
        data = FlowShopInstanceData.from_p(self.p, [(0, 1), (1, 2), (2, 3)])
        assert repr(data) == (
            'FlowShopInstanceData(n=3, m=4, edges=[(0, 1), (1, 2), (2, 3)])'
        )


@pytest.mark.pafssp
class TestPFSSPConstructor:
    @staticmethod
    def test_create_data() -> None:
        inst = INSTANCES['ASM']
        edges = [(e[0], e[1]) for e in inst['edges']]
        data = PermFlowShop.create_data(inst['p'], edges)
        assert isinstance(data, FlowShopInstanceData)
        assert data.p == inst['p']
        assert data.edges == edges
        # Sequential edges by default, as in FlowShopInstanceData.from_p
        p = INSTANCES['SEQ']['p']
        assert PermFlowShop.create_data(p).edges == (
            FlowShopInstanceData.from_p(p).edges
        )
        # Inherited by subclasses
        assert isinstance(PermFlowShop1M.create_data(p), FlowShopInstanceData)

    @staticmethod
    def test_create_data_validation() -> None:
        with pytest.raises(ValueError, match='at least one job'):
            PermFlowShop.create_data([])

    @staticmethod
    @pytest.mark.parametrize('constructive', CONSTRUCTIVES)
    @pytest.mark.parametrize('prob_cls', list(PROBLEM_CLASSES.values()))
    def test_constructor_with_data(
        prob_cls: Type[PermFlowShop], constructive: Any
    ) -> None:
        data = make_data('DPM')
        root = prob_cls(data, constructive=constructive)
        assert type(root) is prob_cls
        assert root.data is data
        sol = root.warmstart()
        expected = EXPECTED[f'DPM|warmstart|{constructive}']
        assert sol.calc_lb_1m() == expected['cost']
        assert starts(sol) == expected['starts']

    @staticmethod
    def test_inline_data_kept_alive() -> None:
        inst = INSTANCES['SEQ']
        edges = [(e[0], e[1]) for e in inst['edges']]
        # The root holds the only reference to its data
        root = PermFlowShop(PermFlowShop.create_data(inst['p'], edges))
        gc.collect()
        assert root.data is not None
        expected = EXPECTED['SEQ|warmstart|neh']
        assert root.warmstart().calc_lb_1m() == expected['cost']

    @staticmethod
    @pytest.mark.parametrize('constructive', CONSTRUCTIVES)
    @pytest.mark.parametrize('prob_cls', list(PROBLEM_CLASSES.values()))
    def test_from_p(prob_cls: Type[PermFlowShop], constructive: Any) -> None:
        inst = INSTANCES['DPM']
        edges = [(e[0], e[1]) for e in inst['edges']]
        root = prob_cls.from_p(inst['p'], edges, constructive=constructive)
        assert type(root) is prob_cls
        assert root.data is not None
        assert root.data.p == inst['p']
        assert root.data.edges == edges
        sol = root.warmstart()
        expected = EXPECTED[f'DPM|warmstart|{constructive}']
        assert sol.calc_lb_1m() == expected['cost']
        assert starts(sol) == expected['starts']

    @staticmethod
    def test_from_p_defaults() -> None:
        p = INSTANCES['SEQ']['p']
        root = PermFlowShop.from_p(p)
        assert root.data is not None
        assert root.data.edges == FlowShopInstanceData.from_p(p).edges
        # Each call builds its own instance data
        assert PermFlowShop.from_p(p).data is not root.data
        with pytest.raises(ValueError, match='at least one job'):
            PermFlowShop.from_p([])

    @staticmethod
    def test_from_p_solution_outlives_root() -> None:
        inst = INSTANCES['ASM']
        edges = [(e[0], e[1]) for e in inst['edges']]
        # Root is a temporary: only the solution keeps the data alive
        sol = PermFlowShop.from_p(inst['p'], edges).warmstart()
        gc.collect()
        expected = EXPECTED['ASM|warmstart|neh']
        assert sol.calc_lb_1m() == expected['cost']
        assert starts(sol) == expected['starts']

    @staticmethod
    def test_wrong_data_type() -> None:
        with pytest.raises(TypeError):
            PermFlowShop([[1, 2], [3, 4]])  # type: ignore[arg-type]


@pytest.mark.pafssp
class TestPFSSPLifetime:
    @staticmethod
    def _warmstart_of_dropped_root(
        name: str,
    ) -> tuple[PermFlowShop, 'weakref.ref[FlowShopInstanceData]']:
        root = make_root(name)
        assert root.data is not None
        ref = weakref.ref(root.data)
        return root.warmstart(), ref

    def test_solution_outlives_root(self) -> None:
        sol, ref = self._warmstart_of_dropped_root('ASM')
        gc.collect()
        assert ref() is not None
        assert sol.data is ref()
        expected = EXPECTED['ASM|warmstart|neh']
        assert sol.calc_lb_1m() == expected['cost']
        assert starts(sol) == expected['starts']
        # Instance is released together with the last node
        del sol
        gc.collect()
        assert ref() is None

    @staticmethod
    def test_children_outlive_root() -> None:
        root = make_root('SEQ')
        assert root.data is not None
        ref = weakref.ref(root.data)
        children = root.branch()
        del root
        gc.collect()
        assert ref() is not None
        bounds = [[c.lower_bound_1m(), c.lower_bound_2m()] for c in children]
        assert bounds == EXPECTED['SEQ|bounds|first']
        del children
        gc.collect()
        assert ref() is None

    @staticmethod
    def test_nodes_share_data() -> None:
        root = make_root('DPM')
        data = root.data
        assert data is not None
        nodes = [
            *root.branch(),
            root.copy(),
            root.warmstart(),
            root.quick_constructive(),
            root.neh_initialization(),
            root.multistart_initialization(),
            root.iga_initialization(),
            root.randomized_heur(3, 1),
            root.iga_heur(3, 2, 1),
            root.branch()[0].intensify(root.warmstart()),
        ]
        assert all(node.data is data for node in nodes)

    @staticmethod
    def test_data_is_read_only() -> None:
        root = make_root('SEQ')
        with pytest.raises(AttributeError):
            root.data = None  # type: ignore[misc]

    @staticmethod
    @pytest.mark.parametrize(
        'prob_cls', [PermFlowShop, BenchPermFlowShop, PermFlowShop1M]
    )
    def test_subclass_factory(prob_cls: Type[PermFlowShop]) -> None:
        root = prob_cls.from_data(make_data('SEQ'), constructive='quick')
        assert type(root) is prob_cls
        assert all(type(child) is prob_cls for child in root.branch())
        assert type(root.warmstart()) is prob_cls

    @staticmethod
    def test_bare_problem() -> None:
        problem = PermFlowShop()
        assert problem.data is None
        assert not problem.sequence
        with pytest.raises(ValueError, match='no instance data.*from_p'):
            problem.warmstart()
        with pytest.raises(ValueError, match='no instance data'):
            problem.get_mach_graph()

    @staticmethod
    def test_intensify_requires_same_data() -> None:
        node = make_root('SEQ').branch()[0]
        # Same processing times, but a different FlowShopInstanceData
        other = make_root('SEQ').warmstart()
        with pytest.raises(ValueError, match='same FlowShopInstanceData'):
            node.intensify(other)


@pytest.mark.pafssp
class TestPFSSPStartTimes:
    @staticmethod
    @pytest.mark.parametrize('name', NAMES)
    @pytest.mark.parametrize('constructive', CONSTRUCTIVES)
    def test_warmstart_schedule(name: str, constructive: str) -> None:
        sol = make_root(name, constructive=constructive).warmstart()
        check_schedule(sol, name, sol.calc_lb_1m())

    @staticmethod
    @pytest.mark.parametrize('name', NAMES)
    def test_bnb_schedule(name: str) -> None:
        bnb = LazyBnB(make_root(name))
        res = bnb.solve()
        check_schedule(res.problem, name, res.cost)

    @staticmethod
    def test_solutions_do_not_interfere() -> None:
        root = make_root('ASM')
        sol_a = root.neh_initialization()
        sol_b = root.quick_constructive()
        starts_a = starts(sol_a)
        starts_b = starts(sol_b)
        assert starts(sol_a) == starts_a
        assert starts_a == EXPECTED['ASM|warmstart|neh']['starts']
        assert starts_b == EXPECTED['ASM|warmstart|quick']['starts']

    @staticmethod
    def test_no_starts_outside_sequence() -> None:
        root = make_root('SEQ')
        assert all(not job.s for job in root.free_jobs)
        child = root.branch()[0]
        assert all(not job.s for job in child.sigma1.jobs)
        seq = child.sequence
        assert len(seq) == len(INSTANCES['SEQ']['p'])
        assert all(len(job.s) == len(job.p) for job in seq)


@pytest.mark.pafssp
class TestPFSSPRegression:
    @staticmethod
    @pytest.mark.parametrize('name', NAMES)
    @pytest.mark.parametrize('constructive', CONSTRUCTIVES)
    def test_warmstart(name: str, constructive: str) -> None:
        sol = make_root(name, constructive=constructive).warmstart()
        result = summary(sol)
        assert result is not None
        result['starts'] = starts(sol)
        assert result == EXPECTED[f'{name}|warmstart|{constructive}']

    @staticmethod
    @pytest.mark.parametrize('name', NAMES)
    @pytest.mark.parametrize('heuristic', list(HEURISTICS))
    def test_heuristics(name: str, heuristic: str) -> None:
        sol = HEURISTICS[heuristic](make_root(name))
        assert summary(sol) == EXPECTED[f'{name}|{heuristic}']

    @staticmethod
    @pytest.mark.parametrize('name', NAMES)
    def test_partial_starts(name: str) -> None:
        partial = make_root(name).branch()[1].branch()[0]
        assert starts(partial) == EXPECTED[f'{name}|partial_starts']

    @staticmethod
    @pytest.mark.parametrize('name', NAMES)
    def test_bounds(name: str) -> None:
        root = make_root(name)
        assert [
            root.lower_bound_1m(),
            root.lower_bound_2m(),
            root.calc_lb_1m(),
            root.calc_lb_2m(),
        ] == EXPECTED[f'{name}|bounds|root']
        first = []
        for j in range(len(INSTANCES[name]['p'])):
            node = make_root(name)
            node.push_job(j)
            first.append([node.lower_bound_1m(), node.lower_bound_2m()])
        assert first == EXPECTED[f'{name}|bounds|first']

    @staticmethod
    @pytest.mark.parametrize(
        'key', sorted(k for k in EXPECTED if '|bnb|' in k)
    )
    def test_bnb(key: str) -> None:
        name, _, cls_name, solver, constructive = key.split('|')
        problem = make_root(name, PROBLEM_CLASSES[cls_name], constructive)
        bnb = SOLVERS[solver](problem)
        res = bnb.solve()
        result: dict[str, Any] = {'cost': res.cost, 'explored': bnb.explored}
        if 'starts' in EXPECTED[key]:
            result['starts'] = starts(res.problem)
        assert result == EXPECTED[key]

    @staticmethod
    @pytest.mark.parametrize('name', NAMES)
    @pytest.mark.parametrize('delta', [0, 1])
    def test_cutoff(name: str, delta: int) -> None:
        opt = EXPECTED[f'{name}|bnb|PermFlowShop|LazyBnB|neh']['cost']
        bnb = CutoffBnB(make_root(name), opt + delta)
        res = bnb.solve()
        result = {
            'cost': res.cost,
            'explored': bnb.explored,
            'len_seq': len(res.problem.sequence),
        }
        assert result == EXPECTED[f'{name}|cutoff|+{delta}']


def makespan(sol: PermFlowShop) -> int:
    return max(s + p for job in sol.sequence for s, p in zip(job.s, job.p))


def assert_valid_schedule(
    sol: PermFlowShop, p: list[list[int]], edges: list[tuple[int, int]]
) -> None:
    """Start times respect machine precedences within each job and the
    permutation on every machine (including machines without edges)."""
    m = len(p[0])
    seq = sol.sequence
    assert sorted(job.j for job in seq) == list(range(len(p)))
    for job in seq:
        assert job.p == p[job.j]
        assert len(job.s) == m
        for k1, k2 in edges:
            assert job.s[k2] >= job.s[k1] + job.p[k1]
    for prev, nxt in zip(seq, seq[1:]):
        for k in range(m):
            assert nxt.s[k] >= prev.s[k] + prev.p[k]


def brute_force(data: FlowShopInstanceData) -> int:
    """Optimal makespan by enumerating every permutation."""
    best = None
    for order in itertools.permutations(range(data.n)):
        sol = PermFlowShop(data)
        for j in order:
            sol.push_job([job.j for job in sol.free_jobs].index(j))
        value = makespan(sol)
        best = value if best is None else min(best, value)
    assert best is not None
    return best


ALL_SOLVERS: dict[str, Callable[[PermFlowShop], Any]] = {
    **SOLVERS,
    'DFS-out': lambda pr: DepthFirstBnB(pr, eval_node='out'),
    'BrFS-out': lambda pr: BreadthFirstBnB(pr, eval_node='out'),
    'BFS-both': lambda pr: BestFirstBnB(pr, eval_node='both'),
}


@pytest.mark.pafssp
class TestPFSSPEdgeCases:
    @staticmethod
    @pytest.mark.parametrize('constructive', CONSTRUCTIVES)
    @pytest.mark.parametrize('solver', list(ALL_SOLVERS))
    def test_single_job(solver: str, constructive: Any) -> None:
        p = [[3, 4, 2]]
        problem = PermFlowShop.from_p(p, constructive=constructive)
        res = ALL_SOLVERS[solver](problem).solve()
        assert res.status == OptStatus.OPTIMAL
        assert res.cost == sum(p[0])
        assert [job.j for job in res.problem.sequence] == [0]

    @staticmethod
    @pytest.mark.parametrize('n', [1, 2, 3, 4])
    def test_iga_few_jobs(n: int) -> None:
        """Destruction size larger than the number of jobs."""
        rng = random.Random(n)
        p = [[rng.randint(1, 9) for _ in range(3)] for _ in range(n)]
        data = FlowShopInstanceData.from_p(p)
        sol = PermFlowShop(data).iga_initialization()
        assert sorted(job.j for job in sol.sequence) == list(range(n))
        assert sol.solution.cost == makespan(sol)
        res = LazyBnB(PermFlowShop(data, constructive='iga')).solve()
        assert res.cost == brute_force(data)
        heur = PermFlowShop(data).iga_heur(5, 10, 1)
        assert sorted(job.j for job in heur.sequence) == list(range(n))

    @staticmethod
    @pytest.mark.parametrize('solver', list(ALL_SOLVERS))
    def test_single_machine(solver: str) -> None:
        p = [[3], [5], [2], [7]]
        data = FlowShopInstanceData.from_p(p)
        assert data.m == 1
        assert data.edges == []
        res = ALL_SOLVERS[solver](PermFlowShop(data)).solve()
        assert res.cost == sum(row[0] for row in p)
        assert_valid_schedule(res.problem, p, [])

    @staticmethod
    @pytest.mark.parametrize('solver', list(ALL_SOLVERS))
    def test_isolated_machine(solver: str) -> None:
        """Machine 1 has no precedences but still processes every job."""
        p = [[1, 50, 1], [1, 60, 1], [2, 10, 3]]
        edges = [(0, 2)]
        data = FlowShopInstanceData.from_p(p, edges)
        assert data.mach_graph.M == len(p[0])
        assert sorted(data.mach_graph.topo_order) == [0, 1, 2]
        res = ALL_SOLVERS[solver](PermFlowShop(data)).solve()
        assert res.cost == sum(row[1] for row in p)
        assert res.cost == brute_force(data)
        assert_valid_schedule(res.problem, p, edges)

    @staticmethod
    @pytest.mark.parametrize('seed', range(10))
    def test_brute_force(seed: int) -> None:
        rng = random.Random(seed)
        n, m = 5, 3
        p = [[rng.randint(1, 20) for _ in range(m)] for _ in range(n)]
        # Chain or assembly graph
        edges = [(0, 1), (1, 2)] if seed % 2 else [(0, 2), (1, 2)]
        data = FlowShopInstanceData.from_p(p, edges)
        opt = brute_force(data)
        for name, solver in ALL_SOLVERS.items():
            for cls in [PermFlowShop, PermFlowShop1M, BenchPermFlowShop]:
                res = solver(cls(data)).solve()
                assert res.cost == opt, (name, cls.__name__)
                assert_valid_schedule(res.problem, p, edges)
        bench = BenchCutoffBnB(BenchPermFlowShop(data), opt + 1).solve()
        assert bench.cost == opt

    @staticmethod
    @pytest.mark.parametrize(
        'heuristic',
        [
            lambda root: root.iga_initialization(),
            lambda root: root.iga_heur(5, 2, 3),
            lambda root: root.randomized_heur(5, 3),
            lambda root: root.neh_initialization().intensify(
                root.quick_constructive()
            ),
        ],
        ids=['iga_initialization', 'iga_heur', 'randomized_heur', 'intensify'],
    )
    def test_heuristic_solution_cost(
        heuristic: Callable[[PermFlowShop], PermFlowShop],
    ) -> None:
        sol = heuristic(make_root('ASM'))
        assert sol.solution.status == OptStatus.FEASIBLE
        assert sol.solution.cost == makespan(sol)
        assert sol.solution.lb == sol.solution.cost

    @staticmethod
    def test_local_search_solution_cost() -> None:
        quick = make_root('ASM').quick_constructive()
        quick.compute_bound()
        sol = quick.local_search()
        assert sol is not None
        assert sol.solution.cost == makespan(sol)
        assert sol.solution.cost < quick.solution.lb

    @staticmethod
    @pytest.mark.parametrize('j', [-1, 12, 100])
    def test_push_job_out_of_range(j: int) -> None:
        root = make_root('SEQ')
        with pytest.raises(IndexError):
            root.push_job(j)
        # Unchanged
        assert len(root.free_jobs) == len(INSTANCES['SEQ']['p'])

    @staticmethod
    def test_permflowshop1m_never_computes_lb5() -> None:
        for cls, uses_lb5 in [(PermFlowShop, True), (PermFlowShop1M, False)]:
            node = make_root('SEQ', cls).branch()[0]
            node.compute_bound()
            first = node.stronger_bound()
            assert first == node.lower_bound_1m()
            node.upgrade_bound(first)
            second = node.stronger_bound()
            if uses_lb5:
                assert second == node.lower_bound_2m()
            else:
                assert second == first
        explored = {}
        for cls in [PermFlowShop, PermFlowShop1M]:
            bnb = LazyBnB(make_root('SEQ', cls))
            bnb.solve()
            explored[cls] = bnb.explored
        assert explored[PermFlowShop1M] >= explored[PermFlowShop]

    @staticmethod
    def test_delay_lb5() -> None:
        opt = EXPECTED['SEQ|bnb|PermFlowShop|LazyBnB|neh']['cost']
        root = make_root('SEQ')
        assert isinstance(LazyBnB.delay_by_root(root), bool)
        bnb = LazyBnB(root, delay_lb5=True)
        assert bnb.min_lb5_level == len(INSTANCES['SEQ']['p']) // 3 + 1
        assert bnb.solve().cost == opt

    @staticmethod
    def test_copy() -> None:
        node = make_root('SEQ').branch()[2]
        node.compute_bound()
        node.upgrade_bound(node.stronger_bound())
        assert node.simple_upgraded
        deep = node.copy()
        shallow = node.copy(deep=False)
        child = node.child_copy()
        for other in [deep, shallow, child]:
            assert other.data is node.data
            assert [j.j for j in other.sequence] == [
                j.j for j in node.sequence
            ]
        assert deep.solution is not node.solution
        assert deep.solution.lb == node.solution.lb
        assert shallow.solution is node.solution
        assert deep.simple_upgraded
        assert child.solution.status == OptStatus.NO_SOLUTION
        # The permutation is a copy
        deep.push_job(0)
        assert len(deep.free_jobs) == len(node.free_jobs) - 1


@pytest.mark.pafssp
class TestPyJob:
    @staticmethod
    def test_exported_fields() -> None:
        name = 'ASM'
        p = INSTANCES[name]['p']
        m = len(p[0])
        sol = make_root(name).warmstart()
        for job in sol.sequence:
            assert isinstance(job, PyJob)
            assert job.p == p[job.j]
            assert len(job.r) == m
            assert len(job.q) == m
            assert len(job.lat) == m
            assert all(len(row) == m for row in job.lat)
            assert len(job.s) == m
            assert job.T == sum(job.p)
            assert repr(job) == f'Job {job.j}'

    @staticmethod
    def test_t_and_slope() -> None:
        # Palmer slope with m = 3 machines: sum((k - 2) * p_k), k = 1..3
        job = PyJob(j=0, p=[1, 2, 3], r=[0, 1, 3], q=[5, 3, 0], lat=[])
        assert job.T == 6  # noqa: PLR2004
        assert job.slope == (1 - 2) * 1 + (2 - 2) * 2 + (3 - 2) * 3
        even = PyJob(j=1, p=[4, 1, 1, 2], r=[], q=[], lat=[])
        # Same integer formula as the C++ Job::get_slope:
        # weights k - (m + 2) // 2 = k - 3, for k = 1..4
        assert even.slope == (-2) * 4 + (-1) * 1 + 0 * 1 + 1 * 2
        assert even.s == []

    @staticmethod
    def test_frozen() -> None:
        job = make_root('SEQ').sequence[0]
        with pytest.raises(dataclasses.FrozenInstanceError):
            job.j = 3  # type: ignore[misc]

    @staticmethod
    def test_snapshots_outlive_problem() -> None:
        root = make_root('DPM')
        data_ref = weakref.ref(root.data)  # type: ignore[arg-type]
        child = root.branch()[0].branch()[1]
        seq = child.sequence
        free = child.free_jobs
        sigma1, sigma2 = child.sigma1, child.sigma2
        expected = [(job.j, list(job.s)) for job in seq]
        del root, child
        gc.collect()
        assert data_ref() is None
        assert [(job.j, job.s) for job in seq] == expected
        assert all(isinstance(job, PyJob) for job in free)
        assert isinstance(sigma1, PySigma)
        assert len(sigma1.jobs) == 1
        assert len(sigma2.jobs) == 1
        assert len(sigma1.C) == sigma1.m
        assert repr(sigma1) == f'Sigma(m={sigma1.m}, jobs=1)'
