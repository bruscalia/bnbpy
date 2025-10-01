from bnbpy.cython.node import Node
from bnbpy.cython.search import BranchAndBound

HEUR_BASE: int = 100

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
    ) -> None:
        """Initialize LazyBnB algorithm

        Parameters
        ----------
        rtol : float, optional
            Relative tolerance, by default 0.0001

        atol : float, optional
            Absolute tolerance, by default 0.0001

        eval_node : str, optional
            Node evaluation strategy, by default 'in'

        save_tree : bool, optional
            Whether to save tree structure, by default False

        queue_mode : str, optional
            Queue mode ('dfs' or 'cycle'), by default 'dfs'
        """
        ...

    @staticmethod
    def queue_factory(mode: str) -> object:
        """Factory method for creating queue instances

        Parameters
        ----------
        mode : str
            Queue mode ('dfs' or 'cycle')

        Returns
        -------
        object
            Queue instance

        Raises
        ------
        ValueError
            If mode is unknown
        """
        ...

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
    """Subclass derived from `BranchAndBound` with a cutoff value"""

    ub_value: float

    def __init__(
        self,
        ub_value: float,
        rtol: float = 0.0001,
        atol: float = 0.0001,
        eval_node: str = 'in',
        save_tree: bool = False,
        queue_mode: str = 'dfs',
    ) -> None:
        """Initialize CutoffBnB algorithm with upper bound cutoff

        Parameters
        ----------
        ub_value : float
            Upper bound cutoff value

        rtol : float, optional
            Relative tolerance, by default 0.0001

        atol : float, optional
            Absolute tolerance, by default 0.0001

        eval_node : str, optional
            Node evaluation strategy, by default 'in'

        save_tree : bool, optional
            Whether to save tree structure, by default False

        queue_mode : str, optional
            Queue mode ('dfs' or 'cycle'), by default 'dfs'
        """
        ...

class CallbackBnB(LazyBnB):
    """Subclass derived from `BranchAndBound` with `post_eval_callback`
    that solves a 2M lower bound (`problem.bound_upgrade`).

    Additionally there's local search as a `solution_callback` and
    a best bound guided search restart at each `restart_freq` nodes."""

    base_heur_factor: int
    heur_factor: int
    heur_calls: int
    level_restart: int

    def __init__(
        self,
        rtol: float = 0.0001,
        atol: float = 0.0001,
        eval_node: str = 'in',
        save_tree: bool = False,
        queue_mode: str = 'dfs',
        heur_factor: int = HEUR_BASE,
    ) -> None:
        """Initialize CallbackBnB algorithm with heuristic callbacks

        Parameters
        ----------
        rtol : float, optional
            Relative tolerance, by default 0.0001

        atol : float, optional
            Absolute tolerance, by default 0.0001

        eval_node : str, optional
            Node evaluation strategy, by default 'in'

        save_tree : bool, optional
            Whether to save tree structure, by default False

        queue_mode : str, optional
            Queue mode ('dfs' or 'cycle'), by default 'dfs'

        heur_factor : int, optional
            Heuristic factor for intensification, by default HEUR_BASE
        """
        ...

    @staticmethod
    def queue_factory(mode: str) -> object:
        """Factory method for creating queue instances

        Parameters
        ----------
        mode : str
            Queue mode ('dfs' or 'cycle')

        Returns
        -------
        object
            Queue instance

        Raises
        ------
        ValueError
            If mode is unknown
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

def _node_lb(node: Node) -> float:
    """Helper function to get node lower bound

    Parameters
    ----------
    node : Node
        Node to get lower bound from

    Returns
    -------
    float
        Node lower bound
    """
    ...
