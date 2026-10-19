import pyomo.environ as pyo


def positional_model(
    p: list[int], w: list[int], d: list[int]
) -> pyo.ConcreteModel:
    """Positional model for the Total Weighted Tardiness Problem

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

    model = pyo.ConcreteModel()

    # Sets for jobs and positions in the sequence
    model.J = pyo.Set(initialize=range(len(p)))
    model.K = pyo.Set(initialize=range(len(p)))

    # Parameters
    model.p = pyo.Param(model.J, initialize=lambda _, j: p[j])
    model.w = pyo.Param(model.J, initialize=lambda _, j: w[j])
    model.d = pyo.Param(model.J, initialize=lambda _, j: d[j])

    # Big-M of job j in position k: latest completion time of the position
    # without idle times (sum of the k + 1 largest processing times) minus
    # the due date of the job
    largest = sorted(p, reverse=True)
    model.M = pyo.Param(
        model.J,
        model.K,
        initialize=lambda _, j, k: sum(largest[: k + 1]) - d[j],
    )

    # Variables
    model.x = pyo.Var(model.J, model.K, within=pyo.Binary)
    model.C = pyo.Var(model.K, within=pyo.NonNegativeReals)
    model.T = pyo.Var(model.J, within=pyo.NonNegativeReals)

    # Constraints
    model.cstr_position = pyo.Constraint(model.K, rule=cstr_position)
    model.cstr_job = pyo.Constraint(model.J, rule=cstr_job)
    model.cstr_seq = pyo.Constraint(model.K, rule=cstr_seq)
    model.cstr_tardiness = pyo.Constraint(
        model.J, model.K, rule=cstr_tardiness
    )

    # Objective
    model.obj = pyo.Objective(
        expr=sum(model.w[j] * model.T[j] for j in model.J),
        sense=pyo.minimize,
    )

    return model


# Constraints
def cstr_position(model: pyo.ConcreteModel, k: int) -> pyo.Expression:
    return sum(model.x[j, k] for j in model.J) == 1


def cstr_job(model: pyo.ConcreteModel, j: int) -> pyo.Expression:
    return sum(model.x[j, k] for k in model.K) == 1


def cstr_seq(model: pyo.ConcreteModel, k: int) -> pyo.Expression:
    start = 0 if k == model.K.first() else model.C[k - 1]
    return (
        start + sum(model.p[j] * model.x[j, k] for j in model.J) <= model.C[k]
    )


def cstr_tardiness(model: pyo.ConcreteModel, j: int, k: int) -> pyo.Expression:
    # Job j is never late in position k
    if model.M[j, k] <= 0:
        return pyo.Constraint.Skip
    return (
        model.C[k] - model.d[j] - model.M[j, k] * (1 - model.x[j, k])
        <= model.T[j]
    )
