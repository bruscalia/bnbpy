from typing import Any, Collection

import gurobipy as grb

from .job import Job


class GrbTimeIndexedModel:
    """
    Gurobi model for the time-indexed formulation
    of the machine deadline problem.
    """

    # Gurobi model
    _env: grb.Env
    _model: grb.Model

    # Sets
    J: set[int]
    H: list[int]
    S: list[tuple[int, int]]

    # Parameters
    p: dict[int, int]
    w: dict[int, int]
    d: dict[int, int]
    T: int

    # Variables
    x: dict[tuple[int, int], grb.Var]

    # Constraints
    cstr_job: dict[int, grb.Constr]
    cstr_capacity: dict[int, grb.Constr]

    def __init__(self, jobs: Collection[Job]) -> None:
        # Initialize Gurobi model
        self._env = grb.Env()
        self._model = grb.Model(name='MachineDeadlineModel', env=self._env)

        # Build the model
        self.J = {job.id for job in jobs}

        self.p = {job.id: job.p for job in jobs}
        self.w = {job.id: job.w for job in jobs}
        self.d = {job.id: job.d for job in jobs}
        self.T = sum(job.p for job in jobs)

        # Unit time slots [t, t + 1) and start times of each job
        # that meet its deadline
        self.H = list(range(self.T))
        self.S = [
            (j, t) for j in self.J for t in range(last_start(self, j) + 1)
        ]

        self.x = self._model.addVars(self.S, vtype=grb.GRB.BINARY, name='x')

        self.cstr_job = self._model.addConstrs(
            (job_rule(self, j) for j in self.J),
            name='job',
        )
        self.cstr_capacity = self._model.addConstrs(
            (capacity_rule(self, t) for t in self.H),
            name='capacity',
        )

        # Weighted completion time of job j if started at time t
        self._model.setObjective(
            grb.quicksum(
                self.w[j] * (t + self.p[j]) * self.x[j, t] for j, t in self.S
            ),
            grb.GRB.MINIMIZE,
        )
        self._model.update()

    def set_warmstart(self, sequence: list[Job]) -> None:
        t = 0
        for job in sequence:
            # Skip jobs that miss their deadlines in the sequence
            if (job.id, t) in self.x:
                self.x[job.id, t].Start = 1  # type: ignore
            t += job.p

    def solve(self) -> None:
        self._model.optimize()

    def set_param(self, name: str, value: Any) -> None:
        self._model.setParam(name, value)

    def get_param(self, name: str) -> Any:
        return self._model.getParamInfo(name)[2]

    def get_num_nodes(self) -> int:
        return self._model.getAttr(grb.GRB.Attr.NodeCount)  # type: ignore

    def get_ub(self) -> float:
        return self._model.getAttr(grb.GRB.Attr.ObjVal)  # type: ignore

    def get_lb(self) -> float:
        return self._model.getAttr(grb.GRB.Attr.ObjBound)  # type: ignore

    def get_time(self) -> float:
        return self._model.getAttr(grb.GRB.Attr.Runtime)  # type: ignore


def last_start(m: GrbTimeIndexedModel, j: int) -> int:
    # Job j must complete by its deadline and the planning horizon
    return min(m.d[j], m.T) - m.p[j]


def job_rule(m: GrbTimeIndexedModel, j: int) -> Any:
    return grb.quicksum(m.x[j, t] for t in range(last_start(m, j) + 1)) == 1


def capacity_rule(m: GrbTimeIndexedModel, t: int) -> Any:
    # At most one job is processed in slot [t, t + 1), i.e., started
    # between t - p_j + 1 and t, within its feasible start times
    return (
        grb.quicksum(
            m.x[j, s]
            for j in m.J
            for s in range(
                max(0, t - m.p[j] + 1), min(t, last_start(m, j)) + 1
            )
        )
        <= 1
    )
