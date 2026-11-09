import pyomo.environ as pyo


def disjunctive_model(
    p: list[list[int]], edges: list[tuple[int, int]] | None = None
) -> pyo.ConcreteModel:
    """Disjunctive (Manne-type) model for the (assembly) Permutation
    Flow-Shop Scheduling Problem.

    Binary variables ``z[j, k]`` (for ``j < k``) are 1 if job ``j``
    precedes job ``k`` (on every machine, as the sequence is a
    permutation), and ``s[j, m]`` are start times. Precedences between
    machines follow the directed ``edges``.

    Parameters
    ----------
    p : List[List[int]]
        Processing times for each job (row) on each machine (column)

    edges : List[Tuple[int, int]], optional
        Directed edges representing machine precedences,
        by default None (sequential)

    Returns
    -------
    pyo.ConcreteModel
        Pyomo Concrete Model for instance
    """

    if edges is None:
        edges = [(i, i + 1) for i in range(len(p[0]) - 1)]

    model = pyo.ConcreteModel()

    # Sets for machines, edges, jobs, and pairs of jobs
    model.M = pyo.Set(initialize=range(len(p[0])))
    model.E = pyo.Set(initialize=edges, dimen=2)
    model.J = pyo.Set(initialize=range(len(p)))
    n = len(p)
    model.D = pyo.Set(
        initialize=[(j, k) for j in range(n) for k in range(j + 1, n)],
        dimen=2,
    )

    # Parameters (V is a big-M: total processing time)
    model.p = pyo.Param(model.J, model.M, initialize=lambda _, j, m: p[j][m])
    model.V = pyo.Param(initialize=sum(pim for pi in p for pim in pi))

    # Variables
    model.z = pyo.Var(model.D, within=pyo.Binary)
    model.s = pyo.Var(model.J, model.M, within=pyo.NonNegativeReals)
    model.C = pyo.Var(within=pyo.NonNegativeReals)

    # Constraints
    model.cstr_precede = pyo.Constraint(model.J, model.E, rule=cstr_precede)
    model.cstr_before = pyo.Constraint(model.D, model.M, rule=cstr_before)
    model.cstr_after = pyo.Constraint(model.D, model.M, rule=cstr_after)
    model.cstr_total_time = pyo.Constraint(
        model.J, model.M, rule=cstr_total_time
    )

    # Objective
    model.obj = pyo.Objective(expr=model.C, sense=pyo.minimize)

    return model


# Constraints
def cstr_precede(
    model: pyo.ConcreteModel, j: int, m1: int, m2: int
) -> pyo.Expression:
    return model.s[j, m1] + model.p[j, m1] <= model.s[j, m2]


def cstr_before(
    model: pyo.ConcreteModel, j: int, k: int, m: int
) -> pyo.Expression:
    # Job j precedes job k on machine m if z[j, k] = 1
    return model.s[j, m] + model.p[j, m] <= model.s[k, m] + model.V * (
        1 - model.z[j, k]
    )


def cstr_after(
    model: pyo.ConcreteModel, j: int, k: int, m: int
) -> pyo.Expression:
    # Job k precedes job j on machine m if z[j, k] = 0
    return (
        model.s[k, m] + model.p[k, m]
        <= model.s[j, m] + model.V * (model.z[j, k])
    )


def cstr_total_time(
    model: pyo.ConcreteModel, j: int, m: int
) -> pyo.Expression:
    return model.s[j, m] + model.p[j, m] <= model.C
