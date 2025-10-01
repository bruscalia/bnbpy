import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Literal

from bnbpy.cython.node import Node
from bnbpy.cython.search import BranchAndBound

log = logging.getLogger(__name__)


class ParallelBnB(BranchAndBound):
    def __init__(
        self,
        rtol: float = 0.0001,
        atol: float = 0.0001,
        eval_node: Literal['in', 'out', 'both'] = 'out',
        max_workers: int = 4,
    ) -> None:
        super().__init__(rtol, atol, eval_node)
        self.max_workers = max_workers

    def branch(self, node: Node) -> None:
        children = node.branch()
        if children:
            # Use ThreadPoolExecutor for parallel execution
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit compute_bound tasks for each child node
                futures = {
                    executor.submit(child.compute_bound): child
                    for child in children
                }

                # Process the results as they complete
                for future in as_completed(futures):
                    child = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        log.error(f'Error in computing LB for child node: {e}')

                    # Enqueue each child after computing the lower bound
                    self.enqueue(child)
        else:
            self.log_row('Cutoff')
