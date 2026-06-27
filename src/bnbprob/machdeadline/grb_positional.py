from typing import Any, Collection

import gurobipy as grb

from .job import Job


class GrbPositionalModel:
    """
    Gurobi model for the positional formulation
    of the machine deadline problem.
    """

    # Gurobi model
    _env: grb.Env
    _model: grb.Model

    # Sets
    J: set[int]
    K: list[int]

    # Parameters
    p: dict[int, int]
    w: dict[int, int]
    d: dict[int, int]
    M: int

    # Variables
    x: dict[tuple[int, int], grb.Var]
    t: dict[int, grb.Var]
    C: dict[int, grb.Var]

    # Constraints
    cstr_position: dict[int, grb.Constr]
    cstr_job: dict[int, grb.Constr]
    cstr_position_completion: dict[int, grb.Constr]
    cstr_job_completion: dict[tuple[int, int], grb.Constr]
    cstr_deadline: dict[int, grb.Constr]

    def __init__(self, jobs: Collection[Job]) -> None:
        # Initialize Gurobi model
        self._env = grb.Env()
        self._model = grb.Model(name='MachineDeadlineModel', env=self._env)

        # Build the model
        self.J = {job.id for job in jobs}
        self.K = list(range(len(jobs)))

        self.p = {job.id: job.p for job in jobs}
        self.w = {job.id: job.w for job in jobs}
        self.d = {job.id: job.d for job in jobs}
        self.M = sum(job.p for job in jobs)

        self.x = self._model.addVars(
            self.J, self.K, vtype=grb.GRB.BINARY, name='x'
        )
        self.t = self._model.addVars(
            self.K,
            lb=0,
            vtype=grb.GRB.CONTINUOUS,
            name='t',
        )
        self.C = self._model.addVars(
            self.J,
            lb={j: self.p[j] for j in self.J},
            vtype=grb.GRB.CONTINUOUS,
            name='C',
        )

        self.cstr_position = self._model.addConstrs(
            (position_rule(self, k) for k in self.K),
            name='position',
        )
        self.cstr_job = self._model.addConstrs(
            (job_rule(self, j) for j in self.J),
            name='job',
        )
        self.cstr_position_completion = self._model.addConstrs(
            (completion_pos_rule(self, k) for k in self.K),
            name='position_completion',
        )
        self.cstr_job_completion = self._model.addConstrs(
            (job_completion_rule(self, j, k) for j in self.J for k in self.K),
            name='job_completion',
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
        for k, job in enumerate(sequence):
            self.x[job.id, k].Start = 1  # type: ignore

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


def position_rule(m: GrbPositionalModel, k: int) -> Any:
    return sum(m.x[j, k] for j in m.J) == 1


def job_rule(m: GrbPositionalModel, j: int) -> Any:
    return sum(m.x[j, k] for k in m.K) == 1


def completion_pos_rule(m: GrbPositionalModel, k: int) -> Any:
    if k == 0:
        return m.t[k] == sum(m.p[j] * m.x[j, k] for j in m.J)
    return m.t[k] == m.t[k - 1] + sum(m.p[j] * m.x[j, k] for j in m.J)


def job_completion_rule(m: GrbPositionalModel, j: int, k: int) -> Any:
    return m.t[k] <= m.C[j] + m.M * (1 - m.x[j, k])


def deadline_rule(m: GrbPositionalModel, j: int) -> Any:
    return m.C[j] <= m.d[j]
