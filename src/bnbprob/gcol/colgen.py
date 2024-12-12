import logging
from typing import List, Optional, Tuple

import numpy as np
from scipy.optimize import linprog

from bnbprob.gcol.coloring import ColorGraph, ColorHeuristic, DSatur
from bnbprob.gcol.indset import IndepGraph, IndepSetHeur
from bnbprob.milpy.colgen import ColGenMILP, MILPColumn, MILPDuals
from bnbprob.milpy.problem import MILPSol
from bnbpy.colgen import PriceSol, Pricing

log = logging.getLogger(__name__)


def _find_max_node(edges: List[Tuple[int, int]]):
    return max(max(edge) for edge in edges)


class ColorMIPPricing(Pricing):
    A: np.ndarray
    b: np.ndarray
    c: np.ndarray
    bounds: List[Tuple[int, int]]
    integrality: np.ndarray
    presolved: Optional[PriceSol]
    mip_rel_gap: float
    time_limit: Optional[float]

    def __init__(
        self,
        edges: List[Tuple[int, int]],
        price_tol: float = 1e-2,
        mip_rel_gap: float = 1e-4,
        time_limit: Optional[float] = None,
    ) -> None:
        """Pricing problem using Maximum Weighted Independent Set Problem
        and an exact implmentation with `scipy` and HiGHS.

        Parameters
        ----------
        edges : List[Tuple[int, int]]
            Edges of the problem graph.
            Node indexes must start with 0.

        price_tol : float, optional
            Tolerance for reduced costs in pricing problem, by default 1e-2

        mip_rel_gap : float, optional
            GAP tolerance for solver, by default 1e-4

        time_limit : Optional[float], optional
            Time limit for solver, by default None
        """
        super().__init__(price_tol=price_tol)
        N = _find_max_node(edges) + 1
        E = len(edges)
        self.A = np.zeros((E, N))
        self.bounds = [(0, 1) for _ in range(N)]
        self.b = np.ones(E)
        self.c = np.ones(N)
        self.integrality = np.ones(N)
        self.presolved = None
        self.mip_rel_gap = mip_rel_gap
        self.time_limit = time_limit

        for e, (i, j) in enumerate(edges):
            self.A[e, i] = 1.0
            self.A[e, j] = self.A[e, i]

    @property
    def solve_options(self):
        options = {'mip_rel_gap': self.mip_rel_gap}
        if self.time_limit:
            options['time_limit'] = self.time_limit
        return options

    def set_weights(self, c: MILPDuals):
        self.c = -c.ineqlin
        self.presolved = None

    def solve(self):
        if self.presolved is not None:
            print('Presolved', self.presolved.red_cost)
            return self.presolved
        sol = linprog(
            -self.c,
            A_ub=self.A,
            b_ub=self.b,
            bounds=self.bounds,
            integrality=self.integrality,
            options=self.solve_options,
        )
        new_col = MILPColumn(a_ub=-sol.x, c=1.0, bounds=(0, 1))
        self.presolved = PriceSol(1 + sol.fun, new_col)
        return self.presolved


class ColorHeurPricing(Pricing):
    graph: IndepGraph
    heur: IndepSetHeur
    presolved: Optional[PriceSol]

    def __init__(
        self,
        edges: List[Tuple[int, int]],
        heur: Optional[IndepSetHeur] = None,
        price_tol: float = 1e-2,
    ) -> None:
        """Pricing problem using Maximum Weighted Independent Set Problem
        and a heuristic implementation.

        Parameters
        ----------
        edges : List[Tuple[int, int]]
            Edges of the problem graph.
            Node indexes must start with 0.

        heur : Optional[IndepSetHeur], optional
            Heuristic algorithm, by default None

        price_tol : float, optional
            Tolerance for reduced costs in pricing problem, by default 1e-2
        """
        super().__init__(price_tol=price_tol)
        if heur is None:
            heur = IndepSetHeur()
        self.graph = IndepGraph(edges)
        self.heur = heur
        self.presolved = None

    def set_weights(self, c: MILPDuals):
        self.graph.set_weights(-c.ineqlin)
        self.presolved = None

    def solve(self):
        if self.presolved is not None:
            return self.presolved
        sol = self.heur.solve(self.graph)
        nodes = sol.nodes
        cost = sol.cost
        a = np.zeros(len(self.graph.nodes))
        for node in nodes:
            a[node.index] = 1.0
        new_col = MILPColumn(a_ub=-a, c=1.0, bounds=(0, 1))
        self.presolved = PriceSol(1 - cost, new_col)
        return self.presolved


class ColorHybrPricing(Pricing):
    pmip: ColorMIPPricing
    pheur: ColorHeurPricing
    price_tol: float
    presolved: Optional[PriceSol]

    def __init__(
        self,
        edges: List[Tuple[int, int]],
        heur: Optional[IndepSetHeur] = None,
        price_tol: float = 1e-2,
        mip_rel_gap: float = 1e-4,
        time_limit: Optional[float] = None,
    ) -> None:
        """Pricing problem using Maximum Weighted Independent Set Problem
        and a hybric exact/heuristic implmentation with `scipy` and HiGHS.

        Parameters
        ----------
        edges : List[Tuple[int, int]]
            Edges of the problem graph.
            Node indexes must start with 0.

        heur : Optional[IndepSetHeur], optional
            Heuristic algorithm, by default None

        price_tol : float, optional
            Tolerance for reduced costs in pricing problem, by default 1e-2

        mip_rel_gap : float, optional
            GAP tolerance for solver, by default 1e-4

        time_limit : Optional[float], optional
            Time limit for solver, by default None
        """
        super().__init__()
        self.pmip = ColorMIPPricing(
            edges,
            price_tol=price_tol,
            mip_rel_gap=mip_rel_gap,
            time_limit=time_limit,
        )
        self.pheur = ColorHeurPricing(edges, heur=heur, price_tol=price_tol)
        self.price_tol = price_tol
        self.presolved = None

    def set_weights(self, c: MILPDuals):
        self.pmip.set_weights(c)
        self.pheur.set_weights(c)
        self.presolved = None

    def solve(self):
        sol_price = self.pheur.evaluate()
        if sol_price is not None:
            self.presolved = sol_price
            return sol_price
        sol_price = self.pmip.solve()
        return sol_price


class ColGenColor(ColGenMILP):
    """
    Class to solve Graph Coloring problems using a Column Generation
    algorithm based on set cover master problem and maximum weighted
    independent set pricing problem.

    For theory details, refer to the article of Mehrotra & Trick (1996).
    The implementation however differs regarding how the
    Independent Set (price), and Set Cover (master) problems are solved.

    Reference
    ---------
    Mehrotra, A., & Trick, M. A., 1996.
    A column generation approach for graph coloring.
    informs Journal on Computing, 8(4), 344-354.
    """

    def __init__(  # noqa: PLR0913, PLR0917
        self,
        edges: List[Tuple[int, int]],
        color_heur: ColorHeuristic = None,
        pricing: Optional[Pricing] = None,
        max_iter_price: Optional[int] = None,
        branching: str = 'max',
        tol: float = 1e-4,
    ):
        """
        Class to solve Graph Coloring problems using a Column Generation
        algorithm based on set cover master problem and maximum weighted
        independent set pricing problem.

        Parameters
        ----------
        edges : List[Tuple[int, int]]
            Edges of the problem graph.
            Node indexes must start with 0.

        color_heur : ColorHeuristic, optional
            Instance of heuristic to solve graph coloring problem.
            Used as warmstart. By default None

        max_iter_price : Optional[int], optional
            Maximum number of pricing iterations (per node), by default None

        branching : str, optional
            Branching strategy (see `MILP`), by default 'max'

        tol : float, optional
            Integrality tolerance (each variable), by default 1e-4
        """
        # MIP attributes
        N = _find_max_node(edges) + 1
        c = np.ones(N)
        A_ub = -np.eye(N)
        b_ub = -np.ones(N)
        bounds = [(0, 1) for _ in range(N)]
        if pricing is None:
            pricing = ColorHybrPricing(edges, IndepSetHeur, 1e-2)
        super().__init__(
            c,
            A_ub=A_ub,
            b_ub=b_ub,
            bounds=bounds,
            integrality=1,
            pricing=pricing,
            max_iter_price=max_iter_price,
            branching=branching,
            tol=tol,
        )
        self.color_graph = ColorGraph(edges)
        if color_heur is None:
            color_heur = DSatur()
        self.color_heur = color_heur

    def warmstart(self):
        self.color_heur.solve(self.color_graph)
        A = self.columns_from_heur()
        self.milp.A_ub = -A
        self.milp.bounds = [(0, 1) for _ in range(A.shape[1])]
        self.milp.c = np.ones(A.shape[1])

        heur = self.copy()
        heur.milp.compute_bound()
        return heur.solution

    def columns_from_heur(self):
        columns = []
        for c in self.color_graph.colors:
            new_col = np.zeros(len(self.color_graph.nodes))
            for node in c.nodes:
                new_col[node.index] = 1.0
            columns.append(new_col)
        return np.column_stack(columns)


def graph_from_solution(graph: ColorGraph, sol: MILPSol):
    """From a instance of `ColorGraph`, uses the solution of the MILP
    master problem to set node colors

    Parameters
    ----------
    graph : ColorGraph
        Instance of color graph

    sol : MILPSol
        Solution to MILP problem in which columns of A_ub are valid
        independent sets of the graph
    """
    tol = 0.5
    graph.clean()
    cols = [-sol.problem.A_ub[:, j] for j, x in enumerate(sol.x) if x > tol]
    colors = [
        set((int(i) for i in np.nonzero(c > tol)[0].astype(int)))  # noqa: C401
        for c in cols  # noqa: C401
    ]
    for node_set in colors:
        color = graph.add_color()
        for i in node_set:
            node = graph.nodes[i]
            node.set_color(color)
