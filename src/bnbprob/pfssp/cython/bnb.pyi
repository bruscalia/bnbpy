from bnbpy.cython.node import Node
from bnbpy.cython.search import BranchAndBound

RESTART = 10_000

class LazyBnB(BranchAndBound):
    """Subclass derived from `BranchAndBound` with `post_eval_callback`
    that solves a 2M lower bound (`problem.bound_upgrade`)."""

    def __init__(
        self,
        rtol: float = 0.0001,
        atol: float = 0.0001,
        eval_node: str = 'in',
        save_tree: bool = False,
    ): ...
    def post_eval_callback(self, node: Node) -> None: ...

class CallbackBnB(LazyBnB):
    """Subclass derived from `BranchAndBound` with `post_eval_callback`
    that solves a 2M lower bound (`problem.bound_upgrade`).

    Additionally there's local search as a `solution_callback` and
    a best bound guided search restart at each `restart_freq` nodes."""

    def __init__(
        self,
        rtol: float = 0.0001,
        atol: float = 0.0001,
        eval_node: str = 'in',
        save_tree: bool = False,
        restart_freq: int = RESTART,
    ): ...
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
        restart_freq: int = RESTART,
    ): ...
