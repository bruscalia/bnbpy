from typing import Any, Collection

import gurobipy as grb

from .job import Job


class GrbPrecedenceModel:
    """
    Gurobi model for the precedence formulation
    of the machine deadline problem.
    """

    # Gurobi model
    _env: grb.Env
    _model: grb.Model

    # Sets
    J: set[int]
    E: set[tuple[int, int]]

    # Parameters
    p: dict[int, int]
    w: dict[int, int]
    d: dict[int, int]
    M: int

    # Variables
    x: dict[tuple[int, int], grb.Var]
    C: dict[int, grb.Var]

    # Constraints
    cstr_disjunction: dict[tuple[int, int], grb.Constr]
    cstr_completion: dict[tuple[int, int], grb.Constr]
    cstr_deadline: dict[int, grb.Constr]

    def __init__(self, jobs: Collection[Job]) -> None:
        # Initialize Gurobi model
        self._env = grb.Env()
        self._model = grb.Model(name='MachineDeadlineModel', env=self._env)

        # Build the model
        self.J = {job.id for job in jobs}
        self.E = {(i, j) for i in self.J for j in self.J if i != j}
        self.p = {job.id: job.p for job in jobs}

        self.w = {job.id: job.w for job in jobs}
        self.d = {job.id: job.d for job in jobs}
        self.M = sum(job.p for job in jobs)

        self.x = self._model.addVars(self.E, vtype=grb.GRB.BINARY, name='x')
        self.C = self._model.addVars(
            self.J,
            lb={j: self.p[j] for j in self.J},
            vtype=grb.GRB.CONTINUOUS,
            name='C',
        )

        self.cstr_disjunction = self._model.addConstrs(
            (disjunction_rule(self, i, j) for (i, j) in self.E),
            name='disjunction',
        )
        self.cstr_completion = self._model.addConstrs(
            (completion_rule(self, i, j) for (i, j) in self.E),
            name='completion',
        )
        self.cstr_deadline = self._model.addConstrs(
            (deadline_rule(self, j) for j in self.J),
            name='deadline',
        )

        self._model.setObjective(
            grb.quicksum(self.w[j] * self.C[j] for j in self.J),
            grb.GRB.MINIMIZE,
        )
        self._model.update()

    def set_warmstart(self, sequence: list[Job]) -> None:
        for i, job in enumerate(sequence[:-1]):
            for other in sequence[i + 1 :]:
                self.x[job.id, other.id].Start = 1  # type: ignore
                self.x[other.id, job.id].Start = 0  # type: ignore

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


def disjunction_rule(m: GrbPrecedenceModel, i: int, j: int) -> Any:
    return m.x[i, j] + m.x[j, i] == 1


def completion_rule(m: GrbPrecedenceModel, i: int, j: int) -> Any:
    return m.C[i] + m.p[j] <= m.C[j] + m.M * (1 - m.x[i, j])


def deadline_rule(m: GrbPrecedenceModel, j: int) -> Any:
    return m.C[j] <= m.d[j]
