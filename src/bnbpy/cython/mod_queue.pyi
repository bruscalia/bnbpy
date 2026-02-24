from bnbpy.cython.node import Node
from bnbpy.cython.priqueue import BasePriQueue

class MultiDFSQueue(BasePriQueue):

    def __init__(self, restart_freq: int) -> None:
        """Initialize a multi-DFS queue with a specified restart frequency.

        The new queue will start with a single DFS queue at the
        current best bound.

        Parameters
        ----------
        restart_freq : int
            The frequency at which to restart the DFS queues.
        """
        ...

    def not_empty(self) -> bool:
        ...

    def enqueue(self, node: Node) -> None:
        ...

    def dequeue(self) -> Node:
        ...

    def get_lower_bound(self) -> Node:
        ...

    def pop_lower_bound(self) -> Node:
        ...

    def clear(self) -> None:
        ...

class CycleQueue(BasePriQueue):
    """A cycle queue explores sequentially the best-bound
    of each level until the maximum level is reached.
    It then cycles back to the first level and continues.
    """

    def __init__(self) -> None:
        """Initialize a cycle queue.
        """
        ...

    def not_empty(self) -> bool:
        ...

    def enqueue(self, node: Node) -> None:
        ...

    def dequeue(self) -> Node:
        ...

    def get_lower_bound(self) -> Node:
        ...

    def pop_lower_bound(self) -> Node:
        ...

    def clear(self) -> None:
        ...

    def reset_level(self) -> None:
        """Reset the current level to 0."""
        ...
