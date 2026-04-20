from typing import Any, Collection

import pyomo.environ as pyo

from .job import Job


class PrecedenceModel(pyo.ConcreteModel):  # type: ignore
    """
    Pyomo model for the precedence formulation
    of the machine deadline problem.
    """

    # Sets
    J: pyo.Set
    E: pyo.Set

    # Parameters
    p: pyo.Param
    w: pyo.Param
    d: pyo.Param
    M: pyo.Param

    # Variables
    x: pyo.Var
    C: pyo.Var

    # Constraints
    cstr_disjunction: pyo.Constraint
    cstr_completion: pyo.Constraint
    cstr_deadline: pyo.Constraint

    # Objective
    obj: pyo.Objective

    @staticmethod
    def build(jobs: Collection[Job]) -> 'PrecedenceModel':
        """Builds the Pyomo model for the given collection of jobs."""
        return _build_precedence_model(jobs)


def _build_precedence_model(jobs: Collection[Job]) -> PrecedenceModel:
    model = PrecedenceModel()

    # Sets
    model.J = pyo.Set(initialize=[job.id for job in jobs])
    model.E = pyo.Set(
        initialize=[(i, j) for i in model.J for j in model.J if i != j]
    )

    # Parameters
    model.p = pyo.Param(model.J, initialize={job.id: job.p for job in jobs})
    model.w = pyo.Param(model.J, initialize={job.id: job.w for job in jobs})
    model.d = pyo.Param(model.J, initialize={job.id: job.d for job in jobs})
    model.M = pyo.Param(initialize=sum(job.p for job in jobs))

    # Variables
    model.x = pyo.Var(model.E, domain=pyo.Binary)
    model.C = pyo.Var(
        model.J,
        domain=pyo.NonNegativeReals,
        bounds={job.id: (job.p, model.M) for job in jobs},
    )

    # Constraints
    model.cstr_disjunction = pyo.Constraint(model.E, rule=disjunction_rule)
    model.cstr_completion = pyo.Constraint(model.E, rule=completion_rule)
    model.cstr_deadline = pyo.Constraint(model.J, rule=deadline_rule)

    # Objective
    model.obj = pyo.Objective(
        expr=sum(model.w[j] * model.C[j] for j in model.J), sense=pyo.minimize
    )

    return model


def disjunction_rule(m: PrecedenceModel, i: int, j: int) -> Any:
    return m.x[i, j] + m.x[j, i] == 1


def completion_rule(m: PrecedenceModel, i: int, j: int) -> Any:
    return m.C[j] + m.p[i] <= m.C[i] + m.M * (1 - m.x[i, j])


def deadline_rule(m: PrecedenceModel, j: int) -> Any:
    return m.C[j] <= m.d[j]
