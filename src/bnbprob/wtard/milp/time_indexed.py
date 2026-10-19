import pyomo.environ as pyo


def time_indexed_model(
    p: list[int], w: list[int], d: list[int]
) -> pyo.ConcreteModel:
    """Time-indexed model for the Total Weighted Tardiness Problem

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

    # Sets for jobs, time slots, and feasible start times of each job
    model.J = pyo.Set(initialize=range(len(p)))
    model.H = pyo.Set(initialize=range(horizon))
    model.S = pyo.Set(
        initialize=[
            (j, t) for j in range(len(p)) for t in range(horizon - p[j] + 1)
        ],
        dimen=2,
    )

    # Parameters
    model.p = pyo.Param(model.J, initialize=lambda _, j: p[j])
    model.T = pyo.Param(initialize=horizon)

    # Weighted tardiness of job j if started at time t
    model.c = pyo.Param(
        model.S, initialize=lambda _, j, t: w[j] * max(t + p[j] - d[j], 0)
    )

    # Variables
    model.x = pyo.Var(model.S, within=pyo.Binary)

    # Constraints
    model.cstr_job = pyo.Constraint(model.J, rule=cstr_job)
    model.cstr_capacity = pyo.Constraint(model.H, rule=cstr_capacity)

    # Objective
    model.obj = pyo.Objective(
        expr=sum(model.c[j, t] * model.x[j, t] for j, t in model.S),
        sense=pyo.minimize,
    )

    return model


# Constraints
def cstr_job(model: pyo.ConcreteModel, j: int) -> pyo.Expression:
    horizon = pyo.value(model.T)
    return sum(model.x[j, t] for t in range(horizon - model.p[j] + 1)) == 1


def cstr_capacity(model: pyo.ConcreteModel, t: int) -> pyo.Expression:
    # At most one job is processed in slot [t, t + 1), i.e., started
    # between t - p_j + 1 and t, within its feasible start times
    horizon = pyo.value(model.T)
    return (
        sum(
            model.x[j, s]
            for j in model.J
            for s in range(
                max(0, t - model.p[j] + 1),
                min(t, horizon - model.p[j]) + 1,
            )
        )
        <= 1
    )
