import pyomo.environ as pyo


def disjunctive_model(
    p: list[int], w: list[int], d: list[int]
) -> pyo.ConcreteModel:
    """Disjunctive model for the Total Weighted Tardiness Problem

    Parameters
    ----------
    p : List[int]
        Processing times for each job

    w : List[int]
        Weights for each job

    d : List[int]
        Due dates for each job

    Returns
    -------
    pyo.ConcreteModel
        Pyomo Concrete Model for instance
    """

    horizon = sum(p)

    model = pyo.ConcreteModel()

    # Sets for jobs and pairs of jobs
    model.J = pyo.Set(initialize=range(len(p)))
    model.P = pyo.Set(
        initialize=[
            (i, j) for i in range(len(p)) for j in range(i + 1, len(p))
        ],
        dimen=2,
    )

    # Parameters
    model.p = pyo.Param(model.J, initialize=lambda _, j: p[j])
    model.w = pyo.Param(model.J, initialize=lambda _, j: w[j])
    model.d = pyo.Param(model.J, initialize=lambda _, j: d[j])
    model.M = pyo.Param(initialize=horizon)

    # Variables
    model.C = pyo.Var(
        model.J,
        within=pyo.NonNegativeReals,
        bounds=lambda _, j: (p[j], horizon),
    )
    model.z = pyo.Var(model.P, within=pyo.Binary)
    model.T = pyo.Var(model.J, within=pyo.NonNegativeReals)

    # Constraints
    model.cstr_precede = pyo.Constraint(model.P, rule=cstr_precede)
    model.cstr_succeed = pyo.Constraint(model.P, rule=cstr_succeed)
    model.cstr_tardiness = pyo.Constraint(model.J, rule=cstr_tardiness)

    # Objective
    model.obj = pyo.Objective(
        expr=sum(model.w[j] * model.T[j] for j in model.J),
        sense=pyo.minimize,
    )

    return model


# Constraints
def cstr_precede(model: pyo.ConcreteModel, i: int, j: int) -> pyo.Expression:
    # Job i precedes job j if z[i, j] == 1
    return model.C[i] + model.p[j] <= model.C[j] + model.M * (
        1 - model.z[i, j]
    )


def cstr_succeed(model: pyo.ConcreteModel, i: int, j: int) -> pyo.Expression:
    # Job j precedes job i if z[i, j] == 0
    return model.C[j] + model.p[i] <= model.C[i] + model.M * model.z[i, j]


def cstr_tardiness(model: pyo.ConcreteModel, j: int) -> pyo.Expression:
    return model.C[j] - model.d[j] <= model.T[j]
