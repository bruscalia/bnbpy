from typing import Any, Collection

import gurobipy as grb


class GrbMaxCliqueModel:
    """
    Gurobi model for the maximum clique problem.
    """

    # Gurobi model
    _env: grb.Env
    _model: grb.Model

    # Sets
    V: set[int]
    E: set[tuple[int, int]]

    # Variables
    x: dict[int, grb.Var]

    # Constraints
    cstr_edges: dict[tuple[int, int], grb.Constr]

    def __init__(self, edges: Collection[tuple[int, int]]) -> None:
        # Initialize Gurobi model
        self._env = grb.Env()
        self._model = grb.Model(name='MaxCliqueModel', env=self._env)

        # Build sets
        nodes: set[int] = set()
        for e in edges:
            nodes.update(e)
        self.V = nodes
        self.E = _find_complement(edges, nodes)

        # Variables
        self.x = self._model.addVars(self.V, vtype=grb.GRB.BINARY, name='x')

        # Constraints
        self.cstr_edges = self._model.addConstrs(
            (edge_constraint_rule(self, i, j) for (i, j) in self.E),
            name='edges',
        )

        # Objective
        self._model.setObjective(
            grb.quicksum(self.x[v] for v in self.V),
            grb.GRB.MAXIMIZE,
        )
        self._model.update()

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


def edge_constraint_rule(m: GrbMaxCliqueModel, i: int, j: int) -> Any:
    return m.x[i] + m.x[j] <= 1
