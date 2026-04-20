from bnbprob.pafssp.cython.problem import BenchPermFlowShop, PermFlowShop
from bnbpy.cython.cbfs import CycleQueue
from bnbpy.cython.node import Node
from bnbpy.cython.priqueue import PriorityQueue
from bnbpy.cython.search import BranchAndBound

HEUR_BASE: int = 100
EVAL_NODE: str

class DfsFlowShop(PriorityQueue[PermFlowShop]):
    """DFS-ordered priority queue for PermFlowShop nodes.

    Priority is ``(-level, lb, idle_time)`` — deepest, then best bound,
    then least idle time first.
    """

    ...

class BestFirstFlowShop(PriorityQueue[PermFlowShop]):
    """Best-first priority queue for PermFlowShop nodes.

    Priority is ``(lb, idle_time)`` — best bound, then least idle time first.
    """

    ...

class CycleBestFlowShop(CycleQueue[PermFlowShop]):
    """Cycle Best First Search node manager specialised for PermFlowShop,
    using :class:`DfsFlowShop`
    as the per-level priority queue.
    """

    ...

class LazyBnB(BranchAndBound[PermFlowShop]):
    """Subclass of :class:`~bnbpy.cython.search.BranchAndBound` with a
    ``post_eval_callback`` that upgrades lower bounds via a 2-machine
    relaxation (``problem.double_bound_upgrade``).

    The search always uses ``eval_node='in'`` and a :class:`DfsFlowShop`
    priority queue.
    """

    delay_lb5: bool
    min_lb5_level: int

    def __init__(
        self,
        problem: PermFlowShop,
        save_tree: bool = False,
        delay_lb5: bool = False,
    ) -> None:
        """Initialise the LazyBnB solver.

        Parameters
        ----------
        problem : PermFlowShop
            Problem instance to solve.

        save_tree : bool, optional
            Whether to preserve tree structure, by default ``False``.

        delay_lb5 : bool, optional
            Delay the two-machine lower-bound upgrade until the node
            reaches a threshold depth, by default ``False``.
        """
        ...

    @staticmethod
    def delay_by_root(problem: PermFlowShop) -> bool:
        """Return ``True`` if the two-machine bound should be delayed.

        Compares the one-machine and two-machine bounds at the root.
        """
        ...

    def post_eval_callback(self, node: Node[PermFlowShop]) -> None:
        """Upgrade lower bounds after node evaluation.

        Calls ``node.c_upgrade_bound()`` (one-machine) and, if the node is
        deep enough, the two-machine upgrade as well.

        Parameters
        ----------
        node : Node[PermFlowShop]
            Node that was just evaluated.
        """
        ...

class CutoffBnB(LazyBnB):
    """Extension of :class:`LazyBnB` that starts with a known upper-bound
    cutoff instead of deriving one from the root heuristic.
    """

    ub_value: float

    def __init__(
        self,
        problem: PermFlowShop,
        ub_value: float,
        save_tree: bool = False,
        delay_lb5: bool = False,
    ) -> None:
        """Initialise CutoffBnB with an explicit upper-bound value.

        Parameters
        ----------
        problem : PermFlowShop
            Problem instance to solve.

        ub_value : float
            Known upper bound; used as the initial incumbent value.

        save_tree : bool, optional
            Whether to preserve tree structure, by default ``False``.

        delay_lb5 : bool, optional
            Delay the two-machine lower-bound upgrade, by default ``False``.
        """
        ...

class BenchCutoffBnB(CutoffBnB):
    """Benchmarking variant of :class:`CutoffBnB`.

    The ``post_eval_callback`` skips the ``update_params`` step so that
    timings for the two-machine bound alone can be measured in isolation.
    """

    def post_eval_callback(self, node: Node[BenchPermFlowShop]) -> None:  # type: ignore[override]
        """Apply only the two-machine bound upgrade (no param update).

        Parameters
        ----------
        node : Node[BenchPermFlowShop]
            Node that was just evaluated.
        """
        ...

class CallbackBnB(LazyBnB):
    """Extension of :class:`LazyBnB` with a primal heuristic and a
    best-bound guided restart strategy.

    *   ``solution_callback`` runs a local search (remove-reinsertion)
        whenever a new incumbent is found.
    *   ``dequeue`` triggers an intensification move every
        ``heur_factor`` explored nodes.
    """

    base_heur_factor: int
    heur_factor: int
    heur_calls: int

    def __init__(
        self,
        problem: PermFlowShop,
        save_tree: bool = False,
        delay_lb5: bool = False,
        heur_factor: int = HEUR_BASE,
    ) -> None:
        """Initialise CallbackBnB.

        Parameters
        ----------
        problem : PermFlowShop
            Problem instance to solve.

        save_tree : bool, optional
            Whether to preserve tree structure, by default ``False``.

        delay_lb5 : bool, optional
            Delay the two-machine lower-bound upgrade, by default ``False``.

        heur_factor : int, optional
            Number of nodes explored between intensification calls,
            by default :data:`HEUR_BASE`.
        """
        ...

    def solution_callback(self, node: Node[PermFlowShop]) -> None:
        """Run a local search heuristic when a new incumbent is found.

        Parameters
        ----------
        node : Node[PermFlowShop]
            Node carrying the new feasible solution.
        """
        ...

    def dequeue(self) -> Node[PermFlowShop]:
        """Dequeue the next node and trigger intensification if due.

        Returns
        -------
        Node[PermFlowShop]
            Next node to process.
        """
        ...

    def intensify(self, node: Node[PermFlowShop]) -> None:
        """Apply a remove-reinsertion local search starting from *node*.

        Updates ``heur_factor`` and ``heur_calls`` based on whether
        improvement was found.

        Parameters
        ----------
        node : Node[PermFlowShop]
            Reference node for the intensification move.
        """
        ...
