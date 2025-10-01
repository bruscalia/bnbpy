__all__ = [
    'is_compiled',
    'plot_tree',
    'Problem',
    'Solution',
    'BranchAndBound',
    'BestFirstBnB',
    'BreadthFirstBnB',
    'DepthFirstBnB',
    'SearchResults',
    'configure_logfile',
    'ColumnGenProblem',
    'Master',
    'MasterSol',
    'PriceSol',
    'Pricing',
    'Node',
]

from logging import getLogger

from bnbpy.colgen import (
    ColumnGenProblem,
    Master,
    MasterSol,
    PriceSol,
    Pricing,
)
from bnbpy.cython.node import Node
from bnbpy.cython.problem import Problem
from bnbpy.cython.search import (
    BestFirstBnB,
    BranchAndBound,
    BreadthFirstBnB,
    DepthFirstBnB,
    SearchResults,
    configure_logfile,
)
from bnbpy.cython.solution import Solution
from bnbpy.plot import plot_tree

log = getLogger(__name__)

try:
    from bnbpy.cython import is_compiled
except (ModuleNotFoundError, ImportError) as e:
    from logging import getLogger
    log = getLogger(__name__)
    log.error('Cython modules not found')
    log.error(e)

    def is_compiled() -> bool:
        return False
