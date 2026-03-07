from bnbprob.pafssp.cython.problem import PermFlowShop
from bnbpy.cython.node import Node
from bnbpy.cython.search import BranchAndBound

HEUR_BASE: int = 100

class LazyBnB(BranchAndBound):
    """Subclass derived from `BranchAndBound` with `post_eval_callback`
    that solves a 2M lower bound (`problem.double_bound_upgrade`)."""

    delay_lb5: bool
    min_lb5_level: int

    def __init__(
        self,
        rtol: float = 0.0001,
        atol: float = 0.0001,
        save_tree: bool = False,
        delay_lb5: bool = False,
    ) -> None:
        """Initialize LazyBnB algorithm

        Parameters
        ----------
        rtol : float, optional
            Relative tolerance, by default 0.0001

        atol : float, optional
            Absolute tolerance, by default 0.0001

        save_tree : bool, optional
            Whether to save tree structure, by default False

        delay_lb5 : bool, optional
            Whether to delay the two-machine lower bound computation,
            by default False
        """
        ...

    @staticmethod
    def delay_by_root(problem: PermFlowShop) -> bool: ...
    def post_eval_callback(self, node: Node) -> None:
        """Callback executed after node evaluation

        Applies bound upgrade to improve lower bound

        Parameters
        ----------
        node : Node
            Node being evaluated
        """
        ...

class CutoffBnB(LazyBnB):
    """Subclass derived from `BranchAndBound` with a cutoff value."""

    ub_value: float

    def __init__(
        self,
        ub_value: float,
        rtol: float = 0.0001,
        atol: float = 0.0001,
        save_tree: bool = False,
        delay_lb5: bool = False,
    ) -> None:
        """Initialize CutoffBnB algorithm with upper bound cutoff.

        Parameters
        ----------
        ub_value : float
            Upper bound cutoff value

        rtol : float, optional
            Relative tolerance, by default 0.0001

        atol : float, optional
            Absolute tolerance, by default 0.0001

        save_tree : bool, optional
            Whether to save tree structure, by default False

        delay_lb5 : bool, optional
            Whether to delay the two-machine lower bound computation,
            by default False
        """
        ...

class BenchCutoffBnB(LazyBnB):
    """Subclass derived from `BranchAndBound` with a cutoff value.
    In this variant the `update_params` is not
    called in the `post_eval_callback`."""

    ...

class CallbackBnB(LazyBnB):
    """Subclass derived from `BranchAndBound` with `post_eval_callback`
    that solves a 2M lower bound (`problem.double_bound_upgrade`).

    Additionally there's local search as a `solution_callback` and
    a best bound guided search restart at each `restart_freq` nodes."""

    base_heur_factor: int
    heur_factor: int
    heur_calls: int

    def __init__(
        self,
        rtol: float = 0.0001,
        atol: float = 0.0001,
        save_tree: bool = False,
        delay_lb5: bool = False,
        heur_factor: int = HEUR_BASE,
    ) -> None:
        """Initialize CallbackBnB algorithm with heuristic callbacks

        Parameters
        ----------
        rtol : float, optional
            Relative tolerance, by default 0.0001

        atol : float, optional
            Absolute tolerance, by default 0.0001

        save_tree : bool, optional
            Whether to save tree structure, by default False

        delay_lb5 : bool, optional
            Whether to delay the two-machine lower bound computation,
            by default False

        heur_factor : int, optional
            Heuristic factor for intensification, by default HEUR_BASE
        """
        ...

    def solution_callback(self, node: Node) -> None:
        """Applies local search with best improvement making
        remove-insertion moves.

        Parameters
        ----------
        node : Node
            Node with new solution
        """
        ...

    def dequeue(self) -> Node:
        """Dequeue next node and apply intensification if needed

        Returns
        -------
        Node
            Next node to process
        """
        ...

    def intensify(self, node: Node) -> None:
        """Apply intensification heuristic to improve solution

        Parameters
        ----------
        node : Node
            Node to intensify
        """
        ...
