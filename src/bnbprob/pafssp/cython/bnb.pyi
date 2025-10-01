from bnbpy.cython.node import Node
from bnbpy.cython.search import BranchAndBound

HEUR_BASE = 100

class LazyBnB(BranchAndBound):
    """Subclass derived from `BranchAndBound` with `post_eval_callback`
    that solves a 2M lower bound (`problem.bound_upgrade`)."""

    def __init__(
        self,
        rtol: float = 0.0001,
        atol: float = 0.0001,
        eval_node: str = 'in',
        save_tree: bool = False,
        queue_mode: str = 'dfs',
    ): ...
    def post_eval_callback(self, node: Node) -> None: ...

class CutoffBnB(LazyBnB):
    """Subclass derived from `BranchAndBound` with a cutoff value"""

    def __init__(  # noqa: PLR0913, PLR0917
        self,
        ub_value: float,
        rtol: float = 0.0001,
        atol: float = 0.0001,
        eval_node: str = 'in',
        save_tree: bool = False,
        queue_mode: str = 'dfs',
    ):
        ...

class CallbackBnB(LazyBnB):
    """Subclass derived from `BranchAndBound` with `post_eval_callback`
    that solves a 2M lower bound (`problem.bound_upgrade`).

    Additionally there's local search as a `solution_callback` and
    a best bound guided search restart at each `restart_freq` nodes."""

    def __init__(  # noqa: PLR0913, PLR0917
        self,
        rtol: float = 0.0001,
        atol: float = 0.0001,
        eval_node: str = 'in',
        save_tree: bool = False,
        queue_mode: str = 'dfs',
        heur_factor: int = HEUR_BASE
    ) -> None:
        ...

    def solution_callback(self, node: Node) -> None:
        """Applies local search with best improvement making
        remove-insertion moves."""
        ...

class CallbackBnBAge(CallbackBnB):
    """Subclass derived from `BranchAndBound` with `post_eval_callback`
    that solves a 2M lower bound (`problem.bound_upgrade`).

    Additionally there's local search as a `solution_callback` and
    a best bound guided search restart at each `restart_freq` nodes
    since last solution."""

    def __init__(
        self,
        rtol: float = 0.0001,
        atol: float = 0.0001,
        eval_node: str = 'in',
        save_tree: bool = False,
        restart_freq: int = 10_000,
    ):
        ...
