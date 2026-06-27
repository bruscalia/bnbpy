from typing import TypeVar

from bnbpy.cython.manager import BaseNodeManager
from bnbpy.cython.node import Node
from bnbpy.cython.problem import Problem

P = TypeVar('P', bound=Problem)

class PriorityManagerTemplate(BaseNodeManager[P]):
    """Abstract priority-queue node manager backed by a native C++ binary heap.

    Stores nodes with ``vector[double]`` priorities; the underlying heap is a
    *min*-heap so the entry with the smallest priority key is dequeued first.

    Subclasses must override :meth:`make_priority` to define the ordering key
    for each node.  All four abstract hooks from :class:`BaseNodeManager`
    (``_enqueue``, ``_dequeue``, ``_filter_by_lb``, ``_clear``) are
    implemented here; only :meth:`make_priority` remains abstract.
    """

    def make_priority(self, node: Node[P]) -> list[float]:
        """Return the ordering key for *node* (smaller → dequeued first).

        Must be implemented by every concrete subclass.

        Parameters
        ----------
        node : Node
            The node about to be enqueued.

        Returns
        -------
        list[float]
            Priority vector.  The heap compares entries lexicographically, so
            ``[a, b]`` is dequeued before ``[c, d]`` when ``a < c``, or when
            ``a == c`` and ``b < d``.

        Raises
        ------
        NotImplementedError
            Always, in the base implementation.
        """
        ...

class BestFirstSearch(PriorityManagerTemplate[P]):
    """Best-first search node manager.

    Dequeues the node with the smallest lower bound first.  Ties are broken
    by tree depth (deeper nodes first) and then by insertion index (earlier
    insertions first).

    Priority key: ``(lb, -level, -index)``
    """

    def make_priority(self, node: Node[P]) -> list[float]:
        """Return the best-first priority key ``(lb, -level, -index)``.

        Parameters
        ----------
        node : Node
            The node being enqueued.

        Returns
        -------
        list[float]
            Three-element priority vector ``[lb, -level, -index]``.
        """
        ...

class DepthFirstSearch(PriorityManagerTemplate[P]):
    """Depth-first search node manager.

    Dequeues the deepest node first.  Among nodes at the same depth, the one
    with the smallest lower bound is dequeued first; ties are broken by
    insertion index (later insertions first, LIFO within a level).

    Priority key: ``(-level, lb, -index)``
    """

    def make_priority(self, node: Node[P]) -> list[float]:
        """Return the depth-first priority key ``(-level, lb, -index)``.

        Parameters
        ----------
        node : Node
            The node being enqueued.

        Returns
        -------
        list[float]
            Three-element priority vector ``[-level, lb, -index]``.
        """
        ...
