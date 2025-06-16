__all__ = [
    'BestFirstBnB',
    'BranchAndBound',
    'BreadthFirstBnB',
    'DepthFirstBnB',
    'configure_logfile',
]

try:
    from bnbpy.cython.search import (
        BestFirstBnB,
        BranchAndBound,
        BreadthFirstBnB,
        DepthFirstBnB,
        configure_logfile,
    )
except (ModuleNotFoundError, ImportError) as e:
    print('Cython Node not found, using Python version')
    print(e)
    from bnbpy.pypure.search import (  # type: ignore
        BestFirstBnB,
        BranchAndBound,
        BreadthFirstBnB,
        DepthFirstBnB,
        configure_logfile,
    )
