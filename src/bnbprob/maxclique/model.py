from typing import Any, Collection

import pyomo.environ as pyo


class MaxCliqueModel(pyo.ConcreteModel):  # type: ignore
    """
    Pyomo model for the maximum clique problem.
    """

    # Sets
    V: pyo.Set
    E: pyo.Set

    # Variables
    x: pyo.Var

    # Constraints
    cstr_edges: pyo.Constraint

    # Objective
    obj: pyo.Objective

    @staticmethod
    def build(edges: Collection[tuple[int, int]]) -> 'MaxCliqueModel':
        """Builds the Pyomo model for the given graph."""
        return _build_max_clique_model(edges)


def _build_max_clique_model(
    edges: Collection[tuple[int, int]],
) -> MaxCliqueModel:
    model = MaxCliqueModel()

    # Sets
    nodes: set[int] = set()
    for e in edges:
        nodes.update(e)
    edges_comp = _find_complement(edges, nodes)

    model.V = pyo.Set(initialize=nodes, ordered=False)
    model.E = pyo.Set(initialize=edges_comp, ordered=False)

    # Variables
    model.x = pyo.Var(model.V, domain=pyo.Binary)

    # Constraints
    model.cstr_edges = pyo.Constraint(model.E, rule=edge_constraint_rule)

    # Objective
    model.obj = pyo.Objective(
        expr=sum(model.x[v] for v in model.V), sense=pyo.maximize
    )

    return model


def _find_complement(
    edges: Collection[tuple[int, int]], nodes: Collection[int]
) -> set[tuple[int, int]]:
    edge_set = set(edges)
    complement = set()
    for i in nodes:
        for j in nodes:
            if i < j and (i, j) not in edge_set and (j, i) not in edge_set:
                complement.add((i, j))
    return complement


def edge_constraint_rule(m: MaxCliqueModel, i: int, j: int) -> Any:
    return m.x[i] + m.x[j] <= 1
