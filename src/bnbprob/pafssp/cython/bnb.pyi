from bnbprob.pafssp.cython.problem import BenchPermFlowShop, PermFlowShop
from bnbpy.cython.levelqueue import CyclicBestSearch, LevelQueue
from bnbpy.cython.node import Node
from bnbpy.cython.primanager import PriorityManagerTemplate
from bnbpy.cython.search import BranchAndBound

EVAL_NODE: str

class DfsFlowShop(PriorityManagerTemplate[PermFlowShop]):
    """DFS-ordered priority queue for PermFlowShop nodes.

    Priority is ``(-level, lb, idle_time)`` — deepest, then best bound,
    then least idle time first.
    """

    ...

class DfsLevelQueue(LevelQueue[PermFlowShop]):
    """Per-level queue for PermFlowShop with best-first priority.

    Priority is ``(lb, idle_time)`` — best bound first, then least idle time.
    """

    ...

class CycleBestFlowShop(CyclicBestSearch[PermFlowShop]):
    """Cyclic best-first search node manager specialised for PermFlowShop,
    using :class:`DfsLevelQueue` as the per-level priority queue.

    With ``max_size`` negative (e.g. ``-1``) the manager starts in
    fallback mode (deepest level first); with ``permanent_fallback=True``
    it never leaves it, which gives a depth-first search with best-first
    order within each level.
    """

    def __init__(
        self,
        max_size: int = 1_000_000,
        permanent_fallback: bool = False,
    ) -> None: ...

class LazyBnB(BranchAndBound[PermFlowShop]):
    """Subclass of :class:`~bnbpy.cython.search.BranchAndBound` with a
    ``post_eval_callback`` that upgrades lower bounds in two stages via
    ``Node.upgrade_bound`` (``PermFlowShop.stronger_bound``): first the
    single-machine bound with updated heads and tails, then the
    two-machine relaxation (LB5), unless the node can already be pruned.

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

        Upgrades the bound with the single-machine relaxation (updated
        heads and tails) and, if the node is still not pruned and deep
        enough (see ``delay_lb5``), with the two-machine relaxation.

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
    """Benchmarking variant of :class:`CutoffBnB`, intended for
    :class:`BenchPermFlowShop` problems.

    The ``post_eval_callback`` skips the ``update_params`` step (already
    done by ``BenchPermFlowShop.calc_bound``) and applies only the
    two-machine bound upgrade, so that its timing can be measured.
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
    *   ``dequeue_callback`` triggers an intensification move every
        ``heur_factor`` explored nodes.
    """

    def __init__(
        self,
        problem: PermFlowShop,
        save_tree: bool = False,
        delay_lb5: bool = False,
        heur_factor: int = 100,
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
            by default 100.
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

    def dequeue_callback(self, node: Node[PermFlowShop]) -> None:
        """Trigger intensification if due (every ``heur_factor``
        explored nodes).

        Parameters
        ----------
        node : Node[PermFlowShop]
            Node that was just dequeued.
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
