"""MILP formulations shipped with the example problems, solved with
HiGHS (pyomo) or Gurobi, against the Branch & Bound implementations."""

import random
from typing import Any

import networkx as nx
import pytest

pyo = pytest.importorskip('pyomo.environ')

from bnbprob.machdeadline import Job, MachDeadlineProb  # noqa: E402
from bnbprob.machdeadline.model import PrecedenceModel  # noqa: E402
from bnbprob.maxclique import Graph, MaxClique, random_graph  # noqa: E402
from bnbprob.maxclique.model import MaxCliqueModel  # noqa: E402
from bnbprob.pafssp import LazyBnB, PermFlowShop  # noqa: E402
from bnbprob.pafssp.mip import (  # noqa: E402
    disjunctive_model,
    positional_model,
)
from bnbpy import BranchAndBound, LifoBnB  # noqa: E402

PAFSSP_CASES = {
    'chain': ([[3, 5, 2], [2, 4, 3], [6, 1, 2], [4, 4, 4]], None),
    'assembly': (
        [[3, 5, 2], [2, 4, 3], [6, 1, 2], [4, 4, 4]],
        [(0, 2), (1, 2)],
    ),
    'isolated': ([[1, 50, 1], [1, 60, 1], [2, 10, 3]], [(0, 2)]),
}


def highs() -> Any:
    solver = pyo.SolverFactory('appsi_highs')
    # The legacy interface raises instead of returning False by default
    if not solver.available(exception_flag=False):
        pytest.skip('HiGHS is not available')
    return solver


def deadline_jobs() -> list[Job]:
    rng = random.Random(3)
    p = [rng.randint(1, 9) for _ in range(5)]
    return [Job(id=j, p=p[j], w=rng.randint(1, 5), d=sum(p)) for j in range(5)]


@pytest.mark.integration
class TestPyomoModels:
    @staticmethod
    @pytest.mark.parametrize('case', list(PAFSSP_CASES))
    @pytest.mark.parametrize('build', [positional_model, disjunctive_model])
    def test_pafssp(case: str, build: Any) -> None:
        p, edges = PAFSSP_CASES[case]
        opt = LazyBnB(PermFlowShop.from_p(p, edges=edges)).solve().cost
        model = build(p, edges)
        highs().solve(model)
        assert pyo.value(model.obj) == pytest.approx(opt)

    @staticmethod
    def test_maxclique() -> None:
        edges = random_graph(15, 0.5, seed=2)
        model = MaxCliqueModel.build(edges)
        highs().solve(model)
        res = LifoBnB(MaxClique(Graph.from_edges(edges))).solve()
        assert pyo.value(model.obj) == pytest.approx(-res.cost)
        _, size = nx.max_weight_clique(nx.Graph(edges), weight=None)
        assert -res.cost == size

    @staticmethod
    def test_machine_deadline() -> None:
        jobs = deadline_jobs()
        model = PrecedenceModel.build(jobs)
        highs().solve(model)
        res = BranchAndBound(MachDeadlineProb(jobs)).solve()
        assert pyo.value(model.obj) == pytest.approx(res.cost)


@pytest.mark.integration
class TestGurobiModels:
    @staticmethod
    @pytest.fixture(autouse=True)
    def _gurobi() -> None:
        pytest.importorskip('gurobipy')

    @staticmethod
    @pytest.mark.parametrize('case', list(PAFSSP_CASES))
    def test_pafssp(case: str) -> None:
        from bnbprob.pafssp.mip.grb_positional import (  # noqa: PLC0415
            GurobiWrapper,
        )

        p, edges = PAFSSP_CASES[case]
        problem = PermFlowShop.from_p(p, edges=edges)
        opt = LazyBnB(problem).solve().cost
        model = GurobiWrapper(p, edges)
        model.set_param('OutputFlag', 0)
        model.set_warmstart(problem)
        model.solve()
        assert model.get_ub() == pytest.approx(opt)
        assert model.get_lb() == pytest.approx(opt)

    @staticmethod
    def test_maxclique() -> None:
        from bnbprob.maxclique.grb_model import (  # noqa: PLC0415
            GrbMaxCliqueModel,
        )

        edges = random_graph(15, 0.5, seed=2)
        model = GrbMaxCliqueModel(edges)
        model.set_param('OutputFlag', 0)
        model.solve()
        res = LifoBnB(MaxClique(Graph.from_edges(edges))).solve()
        assert model.get_ub() == pytest.approx(-res.cost)

    @staticmethod
    @pytest.mark.parametrize('formulation', ['positional', 'precedence'])
    def test_machine_deadline(formulation: str) -> None:
        from bnbprob.machdeadline.grb_positional import (  # noqa: PLC0415
            GrbPositionalModel,
        )
        from bnbprob.machdeadline.grb_precedence import (  # noqa: PLC0415
            GrbPrecedenceModel,
        )

        jobs = deadline_jobs()
        cls = (
            GrbPositionalModel
            if formulation == 'positional'
            else (GrbPrecedenceModel)
        )
        model = cls(jobs)
        model.set_param('OutputFlag', 0)
        model.solve()
        res = BranchAndBound(MachDeadlineProb(jobs)).solve()
        assert model.get_ub() == pytest.approx(res.cost)


def test_isolated_machine_reference() -> None:
    """Machine 1 of the 'isolated' case has no precedences: the optimal
    makespan is its total processing time."""
    p, edges = PAFSSP_CASES['isolated']
    res = LazyBnB(PermFlowShop.from_p(p, edges=edges)).solve()
    assert res.cost == sum(row[1] for row in p)
