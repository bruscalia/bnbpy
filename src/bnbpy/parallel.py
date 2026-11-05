from concurrent.futures import ThreadPoolExecutor
from typing import Literal

from bnbpy.cython.node import Node
from bnbpy.cython.problem import Problem
from bnbpy.cython.search import BranchAndBound


def _compute_bound(node: Node[Problem]) -> None:
    node.compute_bound()


class ParallelBnB(BranchAndBound[Problem]):
    """Branch & Bound that computes the lower bounds of the children of
    each node in a thread pool before enqueueing them.

    Children are then pruned or enqueued (with ``enqueue_callback``)
    exactly as in :class:`BranchAndBound`. Threads only speed up the search
    if ``Problem.calc_bound`` releases the GIL (e.g. calls to external
    solvers or ``nogil`` code).

    Children are always evaluated when branching (as with
    ``eval_node='in'``, but without ``pre_eval_callback`` and
    ``post_eval_callback``, which are not thread-safe in general).
    With ``eval_node='out'`` or ``'both'``, nodes are evaluated again
    after being dequeued.
    """

    def __init__(
        self,
        problem: Problem,
        eval_node: Literal['in', 'out', 'both'] = 'in',
        save_tree: bool = False,
        max_workers: int = 4,
    ) -> None:
        super().__init__(problem, eval_node, save_tree)
        self.max_workers = max_workers

    def branch(self, node: Node[Problem]) -> None:
        children = node.branch()
        if children:
            # Compute the lower bounds of all children in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Exceptions are raised here, in the main thread
                list(executor.map(_compute_bound, children))

            # Enqueue in the original order, so that results are
            # deterministic and equal to the serial search
            for child in children:
                if child.lb < self.ub:
                    self.enqueue_callback(child)
                    self.manager.enqueue(child)
                else:
                    self.prune(child)

        if not self.save_tree and node is not self.root:
            node.cleanup()
        elif self.save_tree:
            node.save_children(children)
