from bnbpy.cython.node import Node
from bnbpy.cython.search import BranchAndBound

HEUR_BASE: int = 100
RESTART: int = 10000

class LazyBnB(BranchAndBound):
    """Subclass derived from `BranchAndBound` with `post_eval_callback`
    that solves a 2M lower bound (`problem.bound_upgrade`).
    """

    def __init__(
        self,
        rtol: float = 1e-4,
        atol: float = 1e-4,
        eval_node: str = 'in',
        save_tree: bool = False,
        queue_mode: str = 'dfs',
    ) -> None:
        """Initialize LazyBnB algorithm.

        Parameters
        ----------
        rtol : float, optional
            Relative tolerance for termination, by default 1e-4
        atol : float, optional
            Absolute tolerance for termination, by default 1e-4
        eval_node : str, optional
            Node evaluation strategy, by default 'in'
        save_tree : bool, optional
            Whether to save node relationships, by default False
        queue_mode : str, optional
            Queue mode ('dfs' or 'cycle'), by default 'dfs'
        """
        ...

    @staticmethod
    def queue_factory(mode: str) -> object:
        """Create queue based on mode.

        Parameters
        ----------
        mode : str
            Queue mode ('dfs' or 'cycle')

        Returns
        -------
        object
            Appropriate queue instance

        Raises
        ------
        ValueError
            If mode is unknown
        """
        ...

    def post_eval_callback(self, node: Node) -> None:
        """Post-evaluation callback that upgrades bounds.

        Parameters
        ----------
        node : Node
            Node to process after evaluation
        """
        ...

class CutoffBnB(LazyBnB):
    """Subclass derived from `BranchAndBound` with a cutoff value"""

    ub_value: float

    def __init__(
        self,
        ub_value: float,
        rtol: float = 1e-4,
        atol: float = 1e-4,
        eval_node: str = 'in',
        save_tree: bool = False,
        queue_mode: str = 'dfs',
    ) -> None:
        """Initialize CutoffBnB with upper bound cutoff.

        Parameters
        ----------
        ub_value : float
            Upper bound cutoff value
        rtol : float, optional
            Relative tolerance for termination, by default 1e-4
        atol : float, optional
            Absolute tolerance for termination, by default 1e-4
        eval_node : str, optional
            Node evaluation strategy, by default 'in'
        save_tree : bool, optional
            Whether to save node relationships, by default False
        queue_mode : str, optional
            Queue mode ('dfs' or 'cycle'), by default 'dfs'
        """
        ...

class CallbackBnB(LazyBnB):
    """Subclass derived from `BranchAndBound` with `post_eval_callback`
    that solves a 2M lower bound (`problem.bound_upgrade`).

    Additionally there's local search as a `solution_callback` and
    a best bound guided search restart at each `restart_freq` nodes.
    """

    restart_freq: int
    base_heur_factor: int
    heur_factor: int
    heur_calls: int
    level_restart: int

    def __init__(
        self,
        rtol: float = 1e-4,
        atol: float = 1e-4,
        eval_node: str = 'in',
        save_tree: bool = False,
        queue_mode: str = 'dfs',
        heur_factor: int = HEUR_BASE
    ) -> None:
        """Initialize CallbackBnB with heuristic callbacks.

        Parameters
        ----------
        rtol : float, optional
            Relative tolerance for termination, by default 1e-4

        atol : float, optional
            Absolute tolerance for termination, by default 1e-4

        eval_node : str, optional
            Node evaluation strategy, by default 'in'

        save_tree : bool, optional
            Whether to save node relationships, by default False

        queue_mode : str, optional
            Queue mode ('dfs' or 'cycle'), by default 'dfs'

        heur_factor : int, optional
            Heuristic factor, by default HEUR_BASE
        """
        ...

    @staticmethod
    def queue_factory(mode: str) -> object:
        """Create queue based on mode.

        Parameters
        ----------
        mode : str
            Queue mode ('dfs' or 'cycle')

        Returns
        -------
        object
            Appropriate queue instance

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
            Node with potential solution to improve
        """
        ...

    def dequeue(self) -> Node:
        """Dequeue next node and apply intensification if needed.

        Returns
        -------
        Node
            Next node to evaluate
        """
        ...

    def intensify(self, node: Node) -> None:
        """Apply intensification procedure to node.

        Parameters
        ----------
        node : Node
            Node to intensify
        """
        ...
