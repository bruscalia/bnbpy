from typing import Any

import gurobipy as grb

from bnbprob.pafssp import PermFlowShop


class GurobiWrapper:
    _model: grb.Model

    # Sets
    M: list[int]
    E: list[tuple[int, int]]
    J: list[int]
    K: list[int]

    # Parameters
    p: list[list[int]]
    V: int

    # Variables
    x: dict[tuple[int, int], grb.Var]
    h: dict[tuple[int, int], grb.Var]
    C: grb.Var

    # Constraints
    cstr_position: dict[int, grb.Constr]
    cstr_job: dict[int, grb.Constr]
    cstr_seq: dict[tuple[int, int], grb.Constr]
    cstr_precede: dict[tuple[int, int, int], grb.Constr]
    cstr_total_time: dict[int, grb.Constr]

    def __init__(
        self, p: list[list[int]], edges: list[tuple[int, int]] | None = None
    ) -> None:
        if edges is None:
            edges = [(i, i + 1) for i in range(len(p[0]) - 1)]

        self._model = grb.Model(name='pafssp')

        # Sets for machines, jobs, horizon, and job sequences
        self.M = list(range(len(p[0])))
        self.E = edges
        self.J = list(range(len(p)))
        self.K = list(range(len(p)))

        # Parameters
        self.p = p
        self.V = sum(pim for pi in p for pim in pi)

        # Variables
        self.x = self._model.addVars(
            ((j, k) for j in self.J for k in self.K),
            vtype=grb.GRB.BINARY,
            name='x',
        )
        self.h = self._model.addVars(
            ((m, k) for m in self.M for k in self.K),
            vtype=grb.GRB.CONTINUOUS,
            name='h',
            lb=0,
        )
        self.C = self._model.addVar(vtype=grb.GRB.CONTINUOUS, name='C', lb=0)

        # Constraints and objective would be added here
        self.cstr_position = self._model.addConstrs(
            cstr_position(self, k) for k in self.K
        )
        self.cstr_job = self._model.addConstrs(
            cstr_job(self, j) for j in self.J
        )
        self.cstr_seq = self._model.addConstrs(
            cstr_seq(self, m, k) for m in self.M for k in self.K
        )
        self.cstr_precede = self._model.addConstrs(
            cstr_precede(self, m1, m2, k)
            for (m1, m2) in self.E
            for k in self.K
        )
        self.cstr_total_time = self._model.addConstrs(
            cstr_total_time(self, m) for m in self.M
        )
        self._model.setObjective(self.C, grb.GRB.MINIMIZE)

    def set_warmstart(self, instance: PermFlowShop) -> None:
        warmstart = instance.warmstart()
        for k, job in enumerate(warmstart.sequence):
            self.x[job.j, k].Start = 1  # type: ignore
        self._model.update()

    def solve(self) -> None:
        self._model.optimize()

    def set_param(self, name: str, value: Any) -> None:
        self._model.setParam(name, value)

    def get_param(self, name: str) -> Any:
        return self._model.getParam(name)

    def get_num_nodes(self) -> int:
        return self._model.getAttr(grb.GRB.Attr.NodeCount)  # type: ignore

    def get_ub(self) -> float:
        return self._model.getAttr(grb.GRB.Attr.ObjVal)  # type: ignore

    def get_lb(self) -> float:
        return self._model.getAttr(grb.GRB.Attr.ObjBound)  # type: ignore

    def get_time(self) -> float:
        return self._model.getAttr(grb.GRB.Attr.Runtime)  # type: ignore


# Constraints
def cstr_position(model: GurobiWrapper, k: int) -> Any:
    return sum(model.x[j, k] for j in model.J) == 1


def cstr_job(model: GurobiWrapper, j: int) -> Any:
    return sum(model.x[j, k] for k in model.K) == 1


def cstr_seq(model: GurobiWrapper, m: int, k: int) -> Any:
    if k == model.K[-1]:
        return True
    return (
        model.h[m, k] + sum(model.p[j][m] * model.x[j, k] for j in model.J)
        <= model.h[m, k + 1]
    )


def cstr_precede(model: GurobiWrapper, m1: int, m2: int, k: int) -> Any:
    return (
        model.h[m1, k] + sum(model.p[j][m1] * model.x[j, k] for j in model.J)
        <= model.h[m2, k]
    )


def cstr_total_time(model: GurobiWrapper, m: int) -> Any:
    k = model.K[-1]
    return (
        model.h[m, k] + sum(model.p[j][m] * model.x[j, k] for j in model.J)
        <= model.C
    )
