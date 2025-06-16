import pyomo.environ as pyo


def disjunctive_model(p: list[list[int]]) -> pyo.ConcreteModel:
    """Positional model for Permutation Flow-Shop Scheduling Problem

    Parameters
    ----------
    p : List[List[int]]
        Processing times for each job

    Returns
    -------
    pyo.ConcreteModel
        Pyomo Concrete Model for instance
    """

    model = pyo.ConcreteModel()

    # Sets for machines, jobs, horizon, and job sequences
    model.M = pyo.Set(initialize=range(len(p[0])))
    model.J = pyo.Set(initialize=range(len(p)))
    model.K = pyo.Set(initialize=range(len(p)))

    # Parameters
    model.p = pyo.Param(model.J, model.M, initialize=lambda _, m, j: p[m][j])
    model.V = pyo.Param(initialize=sum(pim for pi in p for pim in pi))

    # Variables
    model.x = pyo.Var(model.J, model.K, within=pyo.Binary)
    model.h = pyo.Var(model.M, model.K, within=pyo.NonNegativeReals)
    model.C = pyo.Var(within=pyo.NonNegativeReals)

    # Constraints
    model.cstr_position = pyo.Constraint(model.K, rule=cstr_position)
    model.cstr_job = pyo.Constraint(model.K, rule=cstr_job)
    model.cstr_seq = pyo.Constraint(model.M, model.K, rule=cstr_seq)
    model.cstr_precede = pyo.Constraint(model.M, model.K, rule=cstr_precede)
    model.cstr_total_time = pyo.Constraint(model.M, rule=cstr_total_time)

    # Objective
    model.obj = pyo.Objective(expr=model.C, sense=pyo.minimize)

    return model


# Constraints
def cstr_position(model: pyo.ConcreteModel, k: int) -> pyo.Expression:
    return sum(model.x[j, k] for j in model.J) == 1


def cstr_job(model: pyo.ConcreteModel, j: int) -> pyo.Expression:
    return sum(model.x[j, k] for k in model.K) == 1


def cstr_seq(model: pyo.ConcreteModel, m: int, k: int) -> pyo.Expression:
    if k == model.K.last():
        return pyo.Constraint.Skip
    return (
        model.h[m, k] + sum(model.p[j, m] * model.x[j, k] for j in model.J)
        <= model.h[m, k + 1]
    )


def cstr_precede(model: pyo.ConcreteModel, m: int, k: int) -> pyo.Expression:
    if m == model.M.last():
        return pyo.Constraint.Skip
    return (
        model.h[m, k] + sum(model.p[j, m] * model.x[j, k] for j in model.J)
        <= model.h[m + 1, k]
    )


def cstr_comp_precede(
    model: pyo.ConcreteModel, j: int, k: int
) -> pyo.Expression:
    if j == k:
        return model.z[j, k] + model.z[k, j] == 0.0
    return model.z[j, k] + model.z[k, j] == 1.0


def cstr_total_time(model: pyo.ConcreteModel, m: int) -> pyo.Expression:
    k = model.K.last()
    return (
        model.h[m, k] + sum(model.p[j, m] * model.x[j, k] for j in model.J)
        <= model.C
    )
